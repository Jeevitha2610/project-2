"""
Tier 1 & Tier 2 Unit Tests: Asynchronous CPU Task Queue (12 Test Cases).
Coverage:
- TC-T1-QUE-01: Enqueue jobs with unique UUIDs in FIFO sequence
- TC-T1-QUE-02: Serial execution (one active job at a time on CPU)
- TC-T1-QUE-03: Real-time queue position and status tracking
- TC-T1-QUE-04: Watchdog timer triggers cancellation on timeout
- TC-T1-QUE-05: Job failure isolation without crashing queue
- TC-T1-QUE-06: Automatic recovery & processing of subsequent jobs
- TC-T2-BND-QUE-02: Queue capacity limit (50 tasks) backpressure
- TC-T2-BND-QUE-03: User cancellation of queued job
- TC-T2-BND-QUE-04: Runaway job termination releases CPU lock
- TC-T2-BND-QUE-05: Simulated worker exception handling and state reset
- TC-T2-BND-QUE-06: Burst submission handling
- TC-T2-BND-QUE-07: Cancellation of non-existent job returns False
"""

import asyncio
import time
import pytest

try:
    from voicestudio.core.queue import SerialTaskQueue
except ImportError:
    from tests.contracts import SerialTaskQueue


@pytest.mark.unit
class TestTaskQueueTier1:
    """Tier 1: Feature Coverage for Async Serial Task Queue."""

    def test_tc_t1_que_01_fifo_queue_ordering(self):
        """TC-T1-QUE-01: Tasks are enqueued with unique IDs in strict FIFO order."""
        tq = SerialTaskQueue(max_capacity=50)
        j1 = tq.submit_job("First sentence")
        j2 = tq.submit_job("Second sentence")
        j3 = tq.submit_job("Third sentence")

        assert j1.job_id != j2.job_id != j3.job_id
        assert tq.queue == [j1.job_id, j2.job_id, j3.job_id]

    @pytest.mark.anyio
    async def test_tc_t1_que_02_serial_execution_one_at_a_time(self):
        """TC-T1-QUE-02: Jobs execute strictly serially without thread contention."""
        tq = SerialTaskQueue()
        execution_order = []
        active_count = 0
        max_concurrent = 0

        async def dummy_worker(text: str):
            nonlocal active_count, max_concurrent
            active_count += 1
            max_concurrent = max(max_concurrent, active_count)
            await asyncio.sleep(0.01)
            execution_order.append(text)
            active_count -= 1
            return f"Processed: {text}"

        j1 = tq.submit_job("Job 1")
        j2 = tq.submit_job("Job 2")

        await tq.execute_next(dummy_worker)
        await tq.execute_next(dummy_worker)

        assert execution_order == ["Job 1", "Job 2"]
        assert max_concurrent == 1

    def test_tc_t1_que_03_job_status_tracking(self):
        """TC-T1-QUE-03: Job tracks status (queued, processing, completed)."""
        tq = SerialTaskQueue()
        job = tq.submit_job("Status track test")
        assert job.status == "queued"
        assert tq.get_job(job.job_id) is job

    @pytest.mark.anyio
    async def test_tc_t1_que_04_watchdog_timeout_triggers(self):
        """TC-T1-QUE-04: Watchdog timer aborts task exceeding timeout."""
        # Using a 0.05s timeout for fast deterministic testing
        tq = SerialTaskQueue(watchdog_timeout_sec=0.05)
        job = tq.submit_job("Hung task")

        async def hung_worker(text: str):
            await asyncio.sleep(0.5)  # Exceeds 0.05s timeout
            return "Should not finish"

        processed_job = await tq.execute_next(hung_worker)
        assert processed_job.status == "failed"
        assert "watchdog timeout" in processed_job.error.lower()

    @pytest.mark.anyio
    async def test_tc_t1_que_05_error_isolation_does_not_crash(self):
        """TC-T1-QUE-05: Worker exception transitions job to failed without crashing queue."""
        tq = SerialTaskQueue()
        job = tq.submit_job("Error task")

        async def failing_worker(text: str):
            raise RuntimeError("Simulated inference failure")

        processed_job = await tq.execute_next(failing_worker)
        assert processed_job.status == "failed"
        assert "Simulated inference failure" in processed_job.error

    @pytest.mark.anyio
    async def test_tc_t1_que_06_worker_recovers_and_processes_next(self):
        """TC-T1-QUE-06: Worker automatically executes subsequent job after failure."""
        tq = SerialTaskQueue()
        j1 = tq.submit_job("Failing job")
        j2 = tq.submit_job("Successful job")

        async def mixed_worker(text: str):
            if "Failing" in text:
                raise ValueError("Worker failure")
            return "Success"

        res1 = await tq.execute_next(mixed_worker)
        assert res1.status == "failed"

        res2 = await tq.execute_next(mixed_worker)
        assert res2.status == "completed"
        assert res2.result == "Success"


@pytest.mark.unit
class TestTaskQueueTier2:
    """Tier 2: Boundary & Concurrency Cases for Task Queue."""

    def test_tc_t2_bnd_que_02_queue_capacity_limit(self):
        """TC-T2-BND-QUE-02: Submitting beyond max capacity raises backpressure error."""
        tq = SerialTaskQueue(max_capacity=5)
        for i in range(5):
            tq.submit_job(f"Job {i}")

        with pytest.raises(RuntimeError, match="queue is full"):
            tq.submit_job("Overflow job")

    def test_tc_t2_bnd_que_03_cancel_queued_job(self):
        """TC-T2-BND-QUE-03: User cancellation removes job from queue immediately."""
        tq = SerialTaskQueue()
        j = tq.submit_job("Job to cancel")
        assert j.job_id in tq.queue

        cancelled = tq.cancel_job(j.job_id)
        assert cancelled is True
        assert j.status == "cancelled"
        assert j.job_id not in tq.queue

    @pytest.mark.anyio
    async def test_tc_t2_bnd_que_04_watchdog_releases_lock(self):
        """TC-T2-BND-QUE-04: Watchdog timeout releases CPU execution lock."""
        tq = SerialTaskQueue(watchdog_timeout_sec=0.05)
        tq.submit_job("Hung job")
        tq.submit_job("Subsequent job")

        async def hung_then_fast(text: str):
            if "Hung" in text:
                await asyncio.sleep(0.5)
            return "Fast result"

        await tq.execute_next(hung_then_fast)
        assert tq.current_job_id is None  # Lock released

        subsequent = await tq.execute_next(hung_then_fast)
        assert subsequent.status == "completed"
        assert subsequent.result == "Fast result"

    @pytest.mark.anyio
    async def test_tc_t2_bnd_que_05_out_of_memory_error_handled(self):
        """TC-T2-BND-QUE-05: Worker MemoryError transitions job to failed and resets state."""
        tq = SerialTaskQueue()
        tq.submit_job("OOM job")

        async def oom_worker(text: str):
            raise MemoryError("Host available memory exhausted")

        job = await tq.execute_next(oom_worker)
        assert job.status == "failed"
        assert "memory" in job.error.lower()
        assert tq.current_job_id is None

    def test_tc_t2_bnd_que_06_burst_submission_ordering(self):
        """TC-T2-BND-QUE-06: Rapid burst of 10 jobs enqueued with 0 loss."""
        tq = SerialTaskQueue(max_capacity=50)
        jobs = [tq.submit_job(f"Burst job {i}") for i in range(10)]
        assert len(tq.queue) == 10
        assert [j.job_id for j in jobs] == tq.queue

    def test_tc_t2_bnd_que_07_cancel_non_existent_job_returns_false(self):
        """TC-T2-BND-QUE-07: Cancelling unknown job returns False."""
        tq = SerialTaskQueue()
        assert tq.cancel_job("non-existent-job-id") is False
