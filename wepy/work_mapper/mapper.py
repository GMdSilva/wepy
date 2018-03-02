from multiprocessing import Queue, JoinableQueue
import queue

import multiprocessing as mp

from wepy.work_mapper.worker import Worker, Task

PY_MAP = map

class Mapper(object):

    def __init__(self, func, *args, **kwargs):
        self.func = func

    def init(self):
        # nothing to do
        pass

    def cleanup(self):
        # nothing to do
        pass

    def map(self, *args, **kwargs):

        return list(PY_MAP(self.func, *args))

class WorkerMapper(Mapper):

    def __init__(self, func, num_workers, worker_type=None,
                 debug_prints=False):
        self.func = func
        self.num_workers = num_workers
        if worker_type is None:
            self.worker_type = Worker
        else:
            self.worker_type = worker_type

    def init(self, debug_prints=False):
        # Establish communication queues
        self._task_queue = JoinableQueue()
        self._result_queue = Queue()

        # Start workers, giving them all the queues
        self._workers = [self.worker_type(i, self._task_queue, self._result_queue,
                                          debug_prints=debug_prints)
                         for i in range(self.num_workers)]

        # start the worker processes
        for worker in self._workers:
            worker.start()
            if debug_prints:
                print("Worker process started as name: {}; PID: {}".format(worker.name,
                                                                       worker.pid))

    def cleanup(self, debug_prints=False):

        # send poison pills (Stop signals) to the queues to stop them in a nice way
        # and let them finish up
        for i in range(self.num_workers):
            self._task_queue.put((None, None))

        # delete the queues and workers
        self._task_queue = None
        self._result_queue = None
        self._workers = None

    def make_task(self, *args, **kwargs):
        return Task(self.func, *args, **kwargs)

    def map(self, *args, debug_prints=False):

        map_process = mp.current_process()
        if debug_prints:
            print("Mapping from process {}; PID {}".format(map_process.name, map_process.pid))

        # make tuples for the arguments to each function call
        task_args = zip(*args)

        num_tasks = len(args[0])
        # Enqueue the jobs
        for task_idx, task_arg in enumerate(task_args):

            # a task will be the actual task and its task idx so we can
            # sort them later
            self._task_queue.put((task_idx, self.make_task(*task_arg)))


        if debug_prints:
            print("Waiting for tasks to be run")

        # Wait for all of the tasks to finish
        self._task_queue.join()

        # workers_done = [worker.done for worker in self._workers]

        # if all(workers_done):

        # get the results out in an unordered way. We rely on the
        # number of tasks we know we put out because if you just try
        # to get from the queue until it is empty it will just wait
        # forever, since nothing is there. ALternatively it is risky
        # to implement a wait timeout or no wait in case there is a
        # small wait time.
        if debug_prints:
            print("Retrieving results")

        n_results = num_tasks
        results = []
        while n_results > 0:

            if debug_prints:
                print("trying to retrieve result: {}".format(n_results))

            result = self._result_queue.get()
            results.append(result)

            if debug_prints:
                print("Retrieved result {}: {}".format(n_results, result))

            n_results -= 1

        if debug_prints:
            print("No more results")

        if debug_prints:
            print("Retrieved results")

        # sort the results according to their task_idx
        results.sort()

        # then just return the values of the function
        return [result for task_idx, worker_idx, result in results]
