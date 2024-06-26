"""
This module adds support for Asyncio-pygame integration,
it is the bases of basiclly this whole package.
Contains classes for event handlers and creating a Window/event loop.

Classes:

    Window - The core of any asyncUi program, manages the event loop and rendering. Also a Singleton
    EventHandler - An event handler for pygame events, avaliable as a decorator via `eventHandler`
    MethodEventHandler - Similar to `EventHandler`, but for class/unbound functions, constructed via `eventHandlerMethod 

Functions:

    event_handler - decorator, creates an `EventHandler` from a function. Supports infering event type form type hints.
    event_handler_method - creates a `MethodEventHandler`, also supports infering the event type.

"""
import pygame
import asyncio
import time
import warnings
import inspect
import functools
from typing import Protocol, Awaitable, Generic, Callable, TypeVar, Type, Any, TypeVarTuple, Self, overload, Coroutine, Generator, Never, get_type_hints as getTypeHints
from . import events
from contextvars import Context
from dataclasses import dataclass
from types import EllipsisType, TracebackType
from concurrent.futures import Executor, ThreadPoolExecutor

import logging
logger = logging.getLogger(__name__)

#Type vars
T = TypeVar('T')
T2 = TypeVar('T2')
Ts = TypeVarTuple('Ts')
EventT = TypeVar("EventT", bound=events.Event)


__all__ = ('EventHandler', 'EventHandlerMethod', 'event_handler', 'event_handler_method', 'Window', 'Renderer')
class EventHandler(Generic[EventT]):
    """
    Manages registrating and unregistrating of event handlers for the current window

    It can also be used as a context manager to safely register and unregister event handlers.
    It is recommended to use the `eventHandler` decorator to create an event handler

    Methods:
        register - registers the event handler, has no effect if already registered
        unregister - unregisters the event handler, has no effect if already unregistered
        registered - checks if the event handler is currently registered

    """
    def __init__(self, function: Callable[[EventT], None], event_type: Type[EventT]):
        self.function = function
        self.event_type = event_type
    def register(self) -> None:
        if self.registered: 
            return
        Window().register_event_handler(self.event_type, self.function)
    def unregister(self) -> None:
        if not self.registered: 
            return
        Window().unregister_event_handler(self.event_type, self.function)
    @property
    def registered(self) -> bool:
        return Window().is_event_handler_registered(self.event_type, self.function)    
    
    def __enter__(self) -> Self:
        self.register()
        return self
    def __exit__(self, excType: Type[BaseException] | None, excValue: BaseException | None, excTb: TracebackType | None) -> None:
        assert self.registered is True, "An event handler registered by a context manager must be deregistered by a context manager"
        self.unregister()

@overload
def event_handler(event_type: Type[EventT], /) -> Callable[[Callable[[EventT], None]], EventHandler[EventT]]: ...
@overload
def event_handler(event_handler: Callable[[EventT], None], /) -> EventHandler[EventT]: ...

def event_handler(event_type: Type[EventT] | Callable[[EventT], None]) -> Callable[[Callable[[EventT], None]], EventHandler[EventT]] | EventHandler[EventT]: 
    """
    An alternative constructor to `EventHandler`, supports use as a function decorator without type hints or with type hints,
    It is preferred over `EventHandler` directly.

    Examples:

        #Defines an event handler, the event type is inferred from the type hint
        @event_handler
        def printKey(event: events.KeyDown):
            print(event.unicode)

        #Also defines an event handler, but explicity gives the event type
        #This is useful in code bases without type hints or for using arbitrary functions
        @event_handler(events.KeyDown)
        def printKey(event):
            print(event.unicode)
    """
    if isinstance(event_type, type) and issubclass(event_type, events.Event):
        @functools.wraps(event_type)
        def _inner(func: Callable[[EventT], None]) -> EventHandler[EventT]:
            return EventHandler(func, event_type) #type: ignore
        return _inner
    else:
        event_handler = event_type
        #infer the event type based on the type hint
        signature = inspect.signature(event_handler)
            
        arguments = list(signature.parameters.values())
        if len(arguments) != 1:
            raise ValueError("Event handler must take one parameter")
        
        event_argument = arguments[0]
        if event_argument.annotation is event_argument.empty:
            raise ValueError("Event handler must have a type annotation if a type is not specified explicitly")
        event_type = event_argument.annotation
        if not isinstance(event_type, type):
            raise ValueError("Event handler's event annotation must be a valid type")
        if not issubclass(event_type, events.Event):
            raise ValueError("Event handler's evnet annotation must be a subclass of events.Event")
        return EventHandler(event_handler, event_type)

class MethodEventHandler(Generic[T, EventT]):
    """
    A descriptor for managing class/unbound event handlers.

    When used on a class, automatically binds `self` and allows class functions to be used as event handlers.
    It's recommened to use `eventHanlderMethod` to create MethodEventHandler instances
    """
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
        
        #replace the attribute with the new event handler, bypassing this for feature accesses, so
        #cls.handler is cls.handler == True
        setattr(instance, self.name, handler)
        return handler  
    
@overload
def event_handler_method(event_type: Type[EventT], /) -> Callable[[Callable[[T, EventT], None]], MethodEventHandler[T, EventT]]:  ...

@overload
def event_handler_method(handler: Callable[[T, EventT], None], /) -> MethodEventHandler[T, EventT]: ...

def event_handler_method(handler_or_type: Type[EventT] | Callable[[T, EventT], None]) -> MethodEventHandler[T, EventT] | Callable[[Callable[[T, EventT], None]], MethodEventHandler[T, EventT]]:
    """
    Create an event handler from a class method

    The event type can be provided explicitly by passing it as an argument to the decorator,
    or it can be inffered based on the function's type hint.

    Returns an instance of `MethodEventHandler`

    Examples:
        class Example:
            def __init__(self, value: int) -> None:
                self.value = value
            #explicitly provide the event type
            @event_handler_method(events.KeyDown)
            def keyDownHandler(self, event: events.KeyDown) -> None:
                print("value is: ", self.value, ", key down is: ", event.unicode)
            
            #implicitly infer the event type
            @event_handler_method
            def keyUpHandler(self, event: events.KeyUp) -> None:
                print("value is: ", self.value, ", key up is: ", event.unicode)
        
        #create an Example and register it's handlers
        example = Example(5)
        example.keyDownHandler.register()
        example.keyUpHandler.register()

        window.run()
        # Now, when ever you press a key, it will print 'value is: 5, key down is: {the key}',
        # and when you relase the key it'll print 'value is: 5, key up is: {the key}'
        # Notice how `self` is also passed as an argument
    """
    
    if isinstance(handler_or_type, type):
        #if an event type is given explicitly, return a new decorator to create the method handler
        eventType = handler_or_type
        def _inner(handler:Callable[[T, EventT], None]) -> MethodEventHandler[T, EventT]:
            return MethodEventHandler(handler, eventType)
        return _inner
    else:
        #if no event type is speificed, infer it from the function's type hint
        handler = handler_or_type

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
        self.execute_all()
        for timer in self.timers:
            timeUntil = timer.when() - Window().time()

            if timeUntil < soonest:
                soonest = timeUntil

        return soonest
    def execute_all(self) -> None:
        """
        Schedule the execution of all TimedHandles which have timed out
        """
        deadTimers: list[asyncio.TimerHandle] = []
        for timer in self.timers:
            if timer.when() - Window().time() <= 0:
                deadTimers.append(timer)
                Window().post_event(ExecuteCallbackEvent(timer))
        for timer in deadTimers:
            self.timers.remove(timer)
    def cancel(self, timer: asyncio.TimerHandle) -> None:
        if timer in self.timers:
            self.timers.remove(timer)
@dataclass
class ExecuteCallbackEvent(events.Event):
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


class _HasFileNumber(Protocol):
    def fileno(self) -> int: ...
FileDescriptorLike = int | _HasFileNumber
from socket import socket  # noqa: E402


class Renderer:
    """
    Calls a renderering function at a given FPS, accounting for the time to render
    
    Methods:
        stop - stops rendering after the current frame finishes
        running - returns wether or not the renderer is currently running
    """
    def __init__(self, fps: int, renderer: Callable[['Window'], None]) -> None:
        self._running = False
        self.renderer = renderer
        self.fps = fps
    def stop(self) -> None:
        logger.info(f'stopped renderer {self}')
        self._running = False
    def running(self) -> bool:
        return self._running

    async def _runner(self) -> None:
        # The loop that does rendering
        while self._running:
            start = Window().time()
            self.renderer(Window())
            pygame.display.flip()
            end = Window().time()
            await asyncio.sleep(1/self.fps - (end - start))
    def _run(self) -> None:
        # Schedule the rendering loop
        self._running = True
        asyncio.ensure_future(self._runner())

class Window(asyncio.AbstractEventLoop): 
    """
    The currently running window. Manages asyncio events, pygame event handlers, and rendering.
    Is a singleton, accessible by calling Window() with no arguments

    This is the core class of any asyncUi program, it manages the event loop and calls registered evnet handlers.
    It allows for async-await to be used with pygame, allowing asynchronous programming to be used.

    Initalization:
        Window is a singleton, but it must first be initialized, via Window(pygame.Surface, title),
        the surface should be the pygame window, and the title is well, the title.

        After that, the current window can be accessed via Window(), which will return the window instance.
    
    Methods:

        register_event_handler - register an event handler for the given event type
        unregister_event_handler - unregister an event handler for the given event type, throws if that handler is not registered
        is_event_handler_registered - returns wether or not the given event handler is registered for the given event type
        post_event - post a pygame or asyncui event to the pygame event queue
        get_event - asyncshrnously await for the next event of given type

        scale_factor - Returns the scale factor between the current window size and it's initial size
        start_renderer - Takes a render function an FPS and returns a `Renderer` instance, raises if a renderer is already running

        run - run the event loop forever

        refer to asyncio's event loop documentation for other all methods. 
        https://docs.python.org/3/library/asyncio-eventloop.html
    """


    def __init__(self, window: pygame.Surface | EllipsisType = ..., unscaled_size: tuple[int, int] | EllipsisType = ..., title: str | EllipsisType = ...) -> None:
        if window is ...: 
            return
        if title is ...: 
            return
        if unscaled_size is ...:
            return

        pygame.display.set_caption(title)
        self.size = window.get_size()
        self.window = window
        self.event_handlers: dict[int, set[Callable[[Any], None]]] = {}
        self.timers = TimerList()
        self.unscaled_size =  unscaled_size
        self.renderer: Renderer | None = None
        self.default_executor: Executor = ThreadPoolExecutor(5)

        self.register_event_handler(ExecuteCallbackEvent, self._run_execute_callback)
        self.register_event_handler(events.VideoResize, self._resize_handler)

        self.closed= False
        self.running = False
        self.debug = __debug__

        self.error_handler: Callable[[asyncio.AbstractEventLoop, dict[str, Any]], object] | None = None
        asyncio._set_running_loop(self)

    
    #Event handler processing
    def register_event_handler(self, eventType: Type[EventT], handler: Callable[[EventT], None]) -> None:
        logger.debug(f"Registered event handler {handler!r} for event type {eventType.__qualname__!r}")
        """
        Register an event handler for a given event type
        
        The event handler will be executed next time the given event is received
        """
        if eventType.type not in self.event_handlers:
            self.event_handlers[eventType.type] = set()

        self.event_handlers[eventType.type].add(handler)
    def unregister_event_handler(self, eventType: Type[EventT], handler: Callable[[EventT], None]) -> None:
        logger.debug(f"Unregistered event handler {handler!r} for event type {eventType.__qualname__}")
        """
        unregister an event handler for a given event type,
        raises a ValueError if the event handler is not registered
        """
        if eventType.type not in self.event_handlers:
            raise ValueError("No event handlers of {evnetType!r} are registered") 
        if handler not in self.event_handlers[eventType.type]:
            raise ValueError(f"Event handler {handler!r} is not registered")
        
        self.event_handlers[eventType.type].remove(handler)
    def is_event_handler_registered(self, eventType: Type[EventT], handler: Callable[[EventT], None]) -> bool:
        """
        Return whether or not an event handler is registered
        """
        return eventType.type in self.event_handlers and handler in self.event_handlers[eventType.type]
    def post_event(self, event: EventT | pygame.event.Event) -> None:
        """
        Post ether an asyncUi event or an pygame event to the event queue
        """
        if isinstance(event, pygame.event.Event):
            pygame.event.post(event)
        else:
            pygame.event.post(events.to_pygame_event(event))
    

    #aync event handling
    def get_event(self, eventType: Type[EventT]) -> Awaitable[EventT]:
        """Asynchronously await for the next event of given type"""
        event_future = asyncio.Future[EventT]()
        def eventHook(event: EventT) -> None:
            event_future.set_result(event)
            self.unregister_event_handler(eventType, eventHook)
        self.register_event_handler(eventType, eventHook)
        return event_future

    # Renderering
    def _resize_handler(self, event: events.VideoResize) -> None:
        new_height = event.w * (self.unscaled_size[1] / self.unscaled_size[0])
        pygame.display.set_mode((event.w, new_height), self.window.get_flags())

    @property
    def scale_factor(self) -> float:
        """
        Returns the scale factor between the inital window size and it's current size
        """
        return self.window.get_size()[0]/self.unscaled_size[0]

    def start_renderer(self, fps: int, renderer: Callable[['Window'], None]) -> Renderer:
        """
        Starts rendering via the renderer function at the given FPS,
        returning a Rederer instance.
        """
        logger.info(f"created renderer with fps={fps}")
        if self.renderer is not None and self.renderer.running():
            raise RuntimeError("Renderer already running")
        self.renderer = Renderer(fps, renderer)
        self.renderer._run()
        return self.renderer
    
    # Scheduling callbacks for asyncio
    def callSoon(self, callback: Callable[[*Ts], None], *args: *Ts, context: Context | None = None) -> asyncio.Handle:
        handle = asyncio.Handle(callback, args, self, context)
        self.post_event(ExecuteCallbackEvent(handle))
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

    # Time/timeouts
    def _timer_handle_cancelled(self, timer: asyncio.TimerHandle) -> None:
        self.timers.cancel(timer)

    def time(self) -> float:
        return time.monotonic()

    # Exceutors
    def run_in_executor(self, executor: Executor | None, function: Callable[[*Ts], T], *args: *Ts) -> asyncio.Future[T]:
        if executor is None:
            executor = self.default_executor
        return asyncio.wrap_future(executor.submit(function, *args))

    def set_default_executor(self, executor: Executor) -> None:
        self.default_executor.shutdown(cancel_futures=True)
        self.default_executor = executor
    async def shutdown_default_executor(self, timeout: int | None = None) -> None:
        assert timeout is None, "timeout not supported in shutdown executor"
        self.default_executor.shutdown(cancel_futures=True)

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
        return self.debug
    def set_debug(self, value: bool) -> None:
        self.debug = value

    #Running events

    def _run_execute_callback(self, event: ExecuteCallbackEvent) -> None:
        """
        This is the event handler that is used to exacute Handles
        """
        event.handle._run()
    def _handle_event(self, event: events.Event | None) -> None:
        """
        Execaute every event handler assosated with an event
        """
        if event is None:
            return
        if event.type not in self.event_handlers:
            return 
        for handler in frozenset(self.event_handlers[event.type]):
            try:
                handler(event)
            except Exception as e:
                context: dict[str, object] = {}
                context['exception'] = e
                context['event'] = event
                context['handler'] = handler
                self.call_exception_handler(context)

            #self.callSoon(handler, event)

    def _wait_for_event(self) -> events.Event | None:
        soonestEvent = self.timers.soonest()
        if soonestEvent == float('inf'):
            return events.marshal(pygame.event.wait())
        else:
            return events.marshal(pygame.event.wait(int(soonestEvent*1000)))
    def run(self) -> None:
        logger.info(f'{self!r} begain event loop')
        self.running = True
        while self.running:
            self._handle_event(self._wait_for_event())
        logger.info(f'{self!r} stoped event loop')
    run_forever = run

    def run_until_complete(self, future: Generator[Any, None, T] | Awaitable[T]) -> T:
        if isinstance(future, Generator):
            future = asyncio.create_task(future)
        future = asyncio.ensure_future(future)
        
        self.running = True
        future.add_done_callback(lambda f: self.stop())
        self.run()

        # The future should now be done
        return future.result()

    def stop(self) -> None:
        self.running = False
    def is_running(self) -> bool:
        return self.running

    def close(self) -> None:
        #This is a singleton, you can't close a singleton...
        pass
    def is_closed(self) -> bool:
        return self.closed
    
    async def shutdown_asyncgens(self) -> None:
        warnings.warn("I havn't any idea what to do on 'shutdown_asyncgens'")
        pass

    # Exception handling
    def default_exception_handler(self: asyncio.AbstractEventLoop, context: dict[Any, Any]) -> None:
        exception: Exception | None = context.get('exception')
        if exception is not None:
            exception_info = (type(exception), exception, exception.__traceback__)
        else:
            exception_info = None
        
        additional_context: list[str] = []
        for key, value in sorted(context.items()):
            if key in ('exception'): 
                continue
            additional_context.append(f"{key}: {value!r}")

        logger.error('\n'.join(additional_context), exc_info=exception_info)


    def set_exception_handler(self, handler: Callable[[asyncio.AbstractEventLoop, dict[str, Any]], object] | None) -> None: 
        self.error_handler = handler
    def get_exception_handler(self) -> Callable[[asyncio.AbstractEventLoop, dict[str, Any]], object] | None: 
        return self.error_handler if self.error_handler is not None else type(self).default_exception_handler
    def call_exception_handler(self, context: dict[Any, Any]) -> None:
        if self.error_handler is None:
            self.default_exception_handler(context)
        else:
            self.error_handler(self, context)
    

    # Supporting stuff for singletons
    # Init via `Window(windowSurface)`, 
    # Get the current window via `Window()`
    __instance: Self | None = None
    def __new__(cls, window: pygame.Surface | EllipsisType = ..., unscaled_size: tuple[int, int] | EllipsisType = ..., title: str | EllipsisType = ...) -> 'Window':
        #Check if no instance is set
        if cls.__instance is None:
            #if no instance is set, then initiazliation must be happening
            if window is ... or title is ... or unscaled_size is ...:
                raise RuntimeError(f"{__name__} is not initialized")
            self = super().__new__(cls)
            cls.__instance = self
            logger.info(f"created window with size={window.get_size()} and title={title!r}")
            return self
        else:
            #if an instance is set, you can't provide init data.
            if window is not ... or title is not ... or unscaled_size is not ...:
                raise RuntimeError(f"{__name__} is already initialized")
            
            return cls.__instance

    def has_instance(self) -> bool:
        return self.__instance is not None


    # A pile of bullshit I don't know how to implement in pygame
    def add_reader(self, fileno: FileDescriptorLike, callback: Callable[[*Ts], T], *args: *Ts) -> None:
        raise NotImplementedError("pygame event loop does not support readers")
    def remove_reader(self, fileno: FileDescriptorLike) -> bool:
        raise NotImplementedError("pygame event loop does not support readers")
    def add_writer(self, fileno: FileDescriptorLike, callback: Callable[[*Ts], T], *args: *Ts) -> None:
        raise NotImplementedError("pygame event loop does not support writers")
    def remove_writer(self, fileno: FileDescriptorLike) -> bool:
        raise NotImplementedError("pygame event loop does not support writers")
    
    async def sock_recv(self, sock: socket, nbytes: int) -> bytes:
        raise NotImplementedError("pygame event loop does not support sockets")
    async def sock_recv_into(self, sock: socket, buffer: object) -> int:
        raise NotImplementedError("pygame event loop does not support sockets")
    async def sock_recvfrom(self, stock: socket, bufferSize: int) -> tuple[bytes, Any]:
        raise NotImplementedError("pygame event loop does not support sockets")
    async def sock_recvfrom_into(self, stock: socket, buffer: object, nbytes: int = 0) -> tuple[int, Any]:
        raise NotImplementedError("pygame event loop does not support sockets")
    async def sock_sendall(self, stock: socket, data: object) -> None:
        raise NotImplementedError("pygame event loop does not support sockets")
    async def sock_sendto(self, sock: socket, data: object, address: Any) -> int:
            raise NotImplementedError("pygame event loop does not support sockets")
    async def sock_connect(self, sock: socket, address: Any) -> None:
        raise NotImplementedError("pygame event loop does not support sockets")
    async def sock_accept(self, sock: socket) -> Any:
        raise NotImplementedError("pygame event loop does not support sockets")
    async def sock_sendfile(self, sock: socket, file: object, offset: int = 0, count: int | None = None, fallback: bool | None = True) -> int:
        raise NotImplementedError("pygame event loop does not support sockets")

    async def getaddrinfo(self, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError("pygame event loop does not support DNS")
    async def getnameinfo(self, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError("pygame event loop does not support DNS")
    
    async def connect_read_pipe(self, protocol_factory: Any, pipe: Any) -> Any:
        raise NotImplementedError("pygame event loop does not support pipes")
    async def connect_write_pipe(self, protocol_factory: Any, pipe: Any) -> Any:
        raise NotImplementedError("pygame event loop does not support pipes")
    def add_signal_handler(self, signum: int, callback: Callable[..., object], *args: Any) -> None:
        raise NotImplementedError("pygame event loop does not support signal handlers")
    def remove_signal_handler(self, sig: int) -> bool:
        raise NotImplementedError("pygame event loop does not support signal handlers")
    
    async def subprocess_exec(self, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError("pygame event loop does not support subprocesses")
    async def subprocess_shell(self, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError("pygame event loop does not support subprocesses")
    
    async def create_connection(self, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError("pygame event loop does not support creating network connections")
    async def create_datagram_endpoint(self, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError("pygame event loop does not support creating datagram endpoints")
    async def create_unix_connection(self, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError("pygame event loop does not support creating Unix connections")
    async def create_server(self, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError("pygame event loop does not support creating network servers")
    async def create_unix_server(self, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError("pygame event loop does not support creating Unix servers")
    async def connect_accepted_socket(self, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError("pygame event loop does not support connecting accepted sockets")
    
    async def sendfile(self, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError("pygame event loop does not support sendfile")
    async def start_tls(self, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError("pygame event loop does not support start_tls")
    
