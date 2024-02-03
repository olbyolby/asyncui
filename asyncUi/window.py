import pygame
import asyncio
import time
import warnings
import inspect
import functools
import traceback
from typing import Awaitable, Generic, Callable, TypeVar, cast, Type, Any, TypeVarTuple, Self, overload, Coroutine, Generator, Never, get_type_hints as getTypeHints
from . import events
from contextvars import Context
from dataclasses import dataclass
from threading import Lock
from types import EllipsisType, TracebackType
from functools import singledispatch

import logging
logger = logging.getLogger(__name__)

#Type vars
T = TypeVar('T')
T2 = TypeVar('T2')
Ts = TypeVarTuple('Ts')
EventT = TypeVar("EventT", bound=events.Event)



class EventHandler(Generic[EventT]):
    def __init__(self, function: Callable[[EventT], None], eventType: Type[EventT] | None = None):
        self.function = function
        if eventType is not None:
            self.eventType = eventType
        else:
            #infer the event type based on the type hint
            signature = inspect.signature(function)
            
            arguments = list(signature.parameters.values())
            if len(arguments) != 1:
                raise ValueError("Event handler must take one parameter")
            
            eventArgument = arguments[0]
            if eventArgument.annotation is eventArgument.empty:
                raise ValueError("Event handler must have a type annotation if a type is not specified explicitly")
            eventType = eventArgument.annotation
            if not isinstance(eventType, type):
                raise ValueError("Event handler's event annotation must be a valid type")
            if not issubclass(eventType, events.Event):
                raise ValueError("Event handler's evnet annotation must be a subclass of events.Event")

            self.eventType = eventType
    def register(self) -> None:
        if self.registered: return
        Window().registerEventHandler(self.eventType, self.function)
    def unregister(self) -> None:
        if not self.registered: return
        Window().unregisterEventHandler(self.eventType, self.function)
    @property
    def registered(self) -> bool:
        return Window().isEventHandlerRegistered(self.eventType, self.function)    
    
    def __enter__(self) -> Self:
        self.register()
        return self
    def __exit__(self, excType: Type[BaseException] | None, excValue: BaseException | None, excTb: TracebackType | None) -> None:
        assert self.registered is True, "An event handler registered by a context manager must be deregistered by a context manager"
        self.unregister()

@overload
def eventHandler(eventType: Type[EventT], /) -> Callable[[Callable[[EventT], None]], EventHandler[EventT]]: ...
@overload
def eventHandler(eventHandler: Callable[[EventT], None], /) -> EventHandler[EventT]: ...

def eventHandler(eventType: Type[EventT] | Callable[[EventT], None]) -> Callable[[Callable[[EventT], None]], EventHandler[EventT]] | EventHandler[EventT]: 
    """
    An alternative constructor to `EventHandler`, supports use as a function decorator without type hints or with type hints,
    It is preferred over `EventHandler` directly.

    Examples:

        #Defines an event handler, the event type is inferred from the type hint
        @eventHandler
        def printKey(event: events.KeyDown):
            print(event.unicode)

        #Also defines an event handler, but explicity gives the event type
        #This is useful in code bases without type hints or for using arbitrary functions
        @eventHandler(events.KeyDown)
        def printKey(event):
            print(event.unicode)
    """
    if isinstance(eventType, type) and issubclass(eventType, events.Event):
        @functools.wraps(eventType)
        def _inner(func: Callable[[EventT], None]) -> EventHandler[EventT]:
            return EventHandler(func, eventType)
        return _inner
    else:
        return EventHandler(eventType)

class MethodEventHandler(Generic[T, EventT]):
    def __init__(self, eventHandler: Callable[[T, EventT], None], eventType: Type[EventT]):
        self.eventType = eventType
        self.eventHandler = eventHandler
    def __set_name__(self, owner: Type[T2], name: str) -> None:
        self.name = name
    @overload
    def __get__(self, instance: None, owner: Type[T2]) -> Self: ...
    @overload
    def __get__(self, instance: T2, owner: Type[T2]) -> EventHandler[EventT]: ...
    

    def __get__(self, instance: None | T2, owner: Type[T2]) -> Self | EventHandler[EventT]:
        if instance is None:
            return self

        boundHandler: Callable[[EventT], None] = functools.partial(self.eventHandler, instance)
        handler = EventHandler(boundHandler, self.eventType)
        setattr(instance, self.name, handler)
        return handler  
    
@overload
def eventHandlerMethod(eventType: Type[EventT], /) -> Callable[[Callable[[T, EventT], None]], MethodEventHandler[T, EventT]]:  ...

@overload
def eventHandlerMethod(handler: Callable[[T, EventT], None], /) -> MethodEventHandler[T, EventT]: ...

def eventHandlerMethod(handlerOrType: Type[EventT] | Callable[[T, EventT], None]) -> MethodEventHandler[T, EventT] | Callable[[Callable[[T, EventT], None]], MethodEventHandler[T, EventT]]:
    if isinstance(handlerOrType, type):
        eventType = handlerOrType
        def _inner(handler:Callable[[T, EventT], None]) -> MethodEventHandler[T, EventT]:
            return MethodEventHandler(handler, eventType)
        return _inner
    else:
        handler = handlerOrType

        if not inspect.isfunction(handler):
            raise ValueError("A event handler method must be a python function for event type inference(Callable objects are not allowed)")

        signature = inspect.signature(handler)
        
        arguments = signature.parameters
        if len(arguments) != 2:
            raise ValueError("A event handler method must have exactly 2 positional arguments for event type inference(No *args or keyword arguments)")

        eventArgument = list(arguments.keys())[1]

        argumentTypes = getTypeHints(handler)
        if eventArgument not in argumentTypes:
            raise ValueError("The 2nd argument of an event handler method must have a valid type annotation for event type inference")
        
        eventType = argumentTypes[eventArgument]
        if not isinstance(eventType, type):
            raise ValueError(f"annotated type {eventType!r} is not a valid event type for an event method handler")
        if not issubclass(eventType, events.Event):
            raise ValueError(f"inferred/annotated type {eventType!r} is an invalid event type(It must be a subclass of events.Event)")
        
        return MethodEventHandler(handler, eventType)
    

class TimerList:
    """
    This class is used to incapsulate the processing and execution of TimerHandles,
    it can be used by custom event loops to implement timer handling.
    """
    def __init__(self) -> None:
        self.timers: list[asyncio.TimerHandle] = []
    def append(self, timer: asyncio.TimerHandle) -> None:
        """
        Append a timer to the list of scheduled TimerHandles
        """
        self.timers.append(timer)
    def soonest(self) -> float:
        """
        This method does 2 things:
        1) execute all events which haved timedout,
        2) return the time until the soonest event

        The return value is ether infinity if there are no waiting timers,
        or the time in seconds until the next timeout.

        Useful for non-busy waiting for events, wait ether for the next event or next timeout.
        """
        soonest: float = float('inf')
        self.executeAll()
        for timer in self.timers:
            timeUntil = timer.when() - Window().time()

            if timeUntil < soonest:
                soonest = timeUntil

        return soonest
    def executeAll(self) -> None:
        """
        Schedule the execution of all TimedHandles which have timed out
        """
        deadTimers: list[asyncio.TimerHandle] = []
        for timer in self.timers:
            if timer.when() - Window().time() <= 0:
                deadTimers.append(timer)
                Window().postEvent(ExacuteCallbackEvent(timer))
        for timer in deadTimers:
            self.timers.remove(timer)
    def cancel(self, timer: asyncio.TimerHandle) -> None:
        if timer in self.timers:
            self.timers.remove(timer)
@dataclass
class ExacuteCallbackEvent(events.Event):
    """
    This is the event triggered when a callback is scheduled to run,
    should not be used by user code
    """
    handle: asyncio.Handle


def _isEventLoopRunning() -> bool:
    #Why would you use exceptions for control flow?
    #Why must you do this to me, asyncio?
    try: 
        asyncio.get_event_loop()
    except RuntimeError:
        return False
    else:
        return True


class Window(asyncio.AbstractEventLoop): 
    


    def __init__(self, window: pygame.Surface | EllipsisType = ..., title: str | EllipsisType = ...) -> None:
        if window is ...: return
        if title is ...: return

        pygame.display.set_caption(title)
        self.size = window.get_size()
        self.window = window
        self.eventHandlers: dict[int, set[Callable[[Any], None]]] = {}
        self.timers = TimerList()
        self.orginalSize = window.get_size()

        self.registerEventHandler(ExacuteCallbackEvent, self._run_exacute_callback)
        self.registerEventHandler(events.VideoResize, self._resizeHandler)

        self.errorHandler: Callable[['Window', dict[Any, Any]], None] | None = None
        asyncio._set_running_loop(self)
    
    #Event handler processing
    def registerEventHandler(self, eventType: Type[EventT], handler: Callable[[EventT], None]) -> None:
        if eventType.type not in self.eventHandlers:
            self.eventHandlers[eventType.type] = set()

        self.eventHandlers[eventType.type].add(handler)
    def unregisterEventHandler(self, eventType: Type[EventT], handler: Callable[[EventT], None]) -> None:
        if eventType.type not in self.eventHandlers:
            raise ValueError("No event handlers of {evnetType!r} are registered") 
        if handler not in self.eventHandlers[eventType.type]:
            raise ValueError(f"Event handler {handler!r} is not registered")
        
        self.eventHandlers[eventType.type].remove(handler)
    def isEventHandlerRegistered(self, eventType: Type[EventT], handler: Callable[[EventT], None]) -> bool:
        return eventType.type in self.eventHandlers and handler in self.eventHandlers[eventType.type]

    def postEvent(self, eventType: EventT) -> None:
        pygame.event.post(events.toPygameEvent(eventType))
    

    #aync event handling
    def getEvent(self, eventType: Type[EventT]) -> Awaitable[EventT]:
        eventFuture = asyncio.Future[EventT]()
        def eventHook(event: EventT) -> None:
            eventFuture.set_result(event)
            self.unregisterEventHandler(eventType, eventHook)
        self.registerEventHandler(eventType, eventHook)
        return eventFuture

    # Renderering
    def _resizeHandler(self, event: events.VideoResize) -> None:
        newHeight = event.w * (self.orginalSize[1] / self.orginalSize[0])
        pygame.display.set_mode((event.w, newHeight), self.window.get_flags())

    @property
    def scaleFactor(self) -> float:
        return self.window.get_size()[0]/self.orginalSize[0]

    # Scheduling callbacks for asyncio
    def callSoon(self, callback: Callable[[*Ts], None], *args: *Ts, context: Context | None = None) -> asyncio.Handle:
        handle = asyncio.Handle(callback, args, self, context)
        self.postEvent(ExacuteCallbackEvent(handle))
        return handle
    call_soon = callSoon #type: ignore #Type shed's arguments arne't correct, *args should be a TypeVarTuple, not Any
    def callSoonThreadsafe(self, callback: Callable[[*Ts], None], *args: *Ts, context: Context | None = None) -> asyncio.Handle:
        #callSoon is thread safe, since posting events in pygame is also thread safe and that's how callSoon works
        return self.callSoon(callback, *args, context=context)
    call_soon_threadsafe = callSoonThreadsafe #type: ignore #Same reason as call_soon

    def callLater(self, delay: float, callback: Callable[[*Ts], None], *args: *Ts, context: Context | None = None) -> asyncio.TimerHandle:
        return self.callAt(delay + self.time(), callback, *args, context=context)
    call_later = callLater #type: ignore #Same reason as callSoon
    def callAt(self, when: float, callback: Callable[[*Ts], None], *args: *Ts, context: Context | None = None) -> asyncio.TimerHandle:
        handle = asyncio.TimerHandle(when, callback, args, self, context)
        self.timers.append(handle)
        return handle
    call_at = callAt #type: ignore #Same reason as callSoon

    def _timer_handle_cancelled(self, timer: asyncio.TimerHandle) -> None:
        self.timers.cancel(timer)
    # Time
    def time(self) -> float:
        return time.monotonic()

    #Factories 
    def create_future(self) -> asyncio.Future[Any]:
        return asyncio.Future(loop=self)
    def create_task(self, coro: Coroutine[Any, None, T] | Generator[Any, Any, T], *, name: str | None = None, context: Context | None = None) -> asyncio.Task[T]:
        return asyncio.Task(coro, loop=self, name=name, context=context)
    def set_task_factory(*args: Any) -> Never:
        raise NotImplementedError("set_task_factory is not yet supported")
    def get_task_factory(self) -> Never:
        raise NotImplementedError("get_task_factory is not yet supported")
    
    #Compatibility
    def get_debug(self) -> bool:
        return __debug__

    #Running events

    def _run_exacute_callback(self, event: ExacuteCallbackEvent) -> None:
        """
        This is the event handler that is used to exacute Handles
        """
        event.handle._run()
    def _handleEvent(self, event: events.Event) -> None:
        """
        Exactue every event handler assosated with an event
        """
        if event.type not in self.eventHandlers:
            return 
        for handler in frozenset(self.eventHandlers[event.type]):
            handler(event)
            #self.callSoon(handler, event)

    def _waitForEvent(self) -> events.Event:
        soonestEvent = self.timers.soonest()
        if soonestEvent == float('inf'):
            return cast(events.Event, pygame.event.wait())
        else:
            return cast(events.Event, pygame.event.wait(int(soonestEvent*1000)))
    def run(self) -> Never:
        while True:
            self._handleEvent(self._waitForEvent())


    # Exception handling
    def default_exception_handler(self, context: dict[Any, Any]) -> None:
        exception: Exception | None = context.get('exception')
        if exception is not None:
            exceptionInfo = (type(exception), exception, exception.__traceback__)
        else:
            exceptionInfo = None
        
        additionalContext: list[str] = []
        for key, value in sorted(context.items()):
            if key in ('exception'): 
                continue
            additionalContext.append(f"{key}: {value!r}")

        logger.error('\n'.join(additionalContext), exc_info=exceptionInfo)

    #python is stupid and doesn't think Window is valid, and demands "AbstractEventLoop", dispite Window being a subclass of that.
    def set_exception_handler(self, handler: Callable[['Window', dict[Any, Any]], None] | None) -> None: #type: ignore[override]
        self.errorHandler = handler
    def get_exception_handler(self) -> Callable[['Window', dict[Any, Any]], None] | None: #type: ignore[override]
        return self.errorHandler
    def call_exception_handler(self, context: dict[Any, Any]) -> None:
        if self.errorHandler is None:
            self.default_exception_handler(context)
        else:
            self.errorHandler(self, context)

    # Supporting stuff for singletons
    # Init via `Window(windowSurface)`, 
    # Get the current window via `Window()`
    __instance: Self | None = None
    def __new__(cls, window: pygame.Surface | EllipsisType = ..., title: str | EllipsisType = ...) -> 'Window':
        #Check if no instance is set
        if cls.__instance is None:
            #if no instance is set, then initiazliation must be happening
            if window is ... or title is ...:
                raise RuntimeError(f"{__name__} is not initialized")
            self = super().__new__(cls)
            cls.__instance = self
            return self
        else:
            #if an instance is set, you can't provide init data.
            if window is not ... or title is not ...:
                raise RuntimeError(f"{__name__} is already initialized")
            
            return cls.__instance


