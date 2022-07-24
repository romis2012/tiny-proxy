import typing
from multiprocessing import Process

from tests.http_app import run_app


class HttpServerConfig(typing.NamedTuple):
    host: str
    port: int
    ssl_certfile: str = None
    ssl_keyfile: str = None

    def to_dict(self):
        d = {}
        for key, val in self._asdict().items():
            if val is not None:
                d[key] = val
        return d


class HttpServer:
    def __init__(self, config: typing.Iterable[HttpServerConfig]):
        self.config = config
        self.workers = []

    def run(self):
        for cfg in self.config:
            print(f'Starting web server on {cfg.host}:{cfg.port}...')
            p = Process(target=run_app, kwargs=cfg.to_dict())
            self.workers.append(p)

        for p in self.workers:
            p.start()

    def shutdown(self):
        for p in self.workers:
            p.terminate()
