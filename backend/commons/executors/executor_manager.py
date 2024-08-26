from concurrent.futures import ThreadPoolExecutor

class ExecutorManager:
    __instance = None

    def __init__(self):
      self.long_executors = ThreadPoolExecutor(max_workers=10)

    @staticmethod
    def getInstance():
      if ExecutorManager.__instance == None:
        ExecutorManager.__instance = ExecutorManager()
      return ExecutorManager.__instance

    def execute(self, job):
       self.long_executors.submit(job)

    def close(self):
       self.long_executors.shutdown()

