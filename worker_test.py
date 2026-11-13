
import sys
import os
import traceback

print("Python executable:", sys.executable, flush=True)
print("Python version:", sys.version, flush=True)
print("Working directory:", os.getcwd(), flush=True)

try:
    from pyspark import SparkConf, SparkContext

    conf = (
        SparkConf()
        .setMaster("local[1]")
        .setAppName("DetailedWorkerTest")
        .set("spark.pyspark.python", sys.executable)
        .set("spark.python.worker.faulthandler.enabled", "true")
        .set("spark.python.worker.reuse", "false")
    )

    sc = SparkContext(conf=conf)
    sc.setLogLevel("ERROR")

    print("Spark started successfully.", flush=True)

    result = sc.parallelize([1, 2, 3], 1).map(
        lambda number: number * 2
    ).collect()

    print("Worker test result:", result, flush=True)

    sc.stop()

except Exception:
    traceback.print_exc()
    raise
