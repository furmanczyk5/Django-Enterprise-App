from celery.result import AsyncResult

def poll_task_progress(task_id):
    # assumes all tasks are equal length

    fraction_complete = 0.0
    message = ""

    try:
        task = AsyncResult(task_id)
        state = task.state

        if state == "SUCCESS":
            fraction_complete = 1.0
            message = "Complete"
        elif state == "FAILURE":
            fraction_complete = 1.0
            message = "Failed"
        elif state == "REVOKED":
            fraction_complete = 1.0
            message = "Revoked"
        elif state == "PROGRESS" and task.result:
            total = task.result.get("total", 1)
            complete = task.result.get("complete", 1)
            message = task.result.get("message", "")
            fraction_complete += (complete/total)
        else:
            # PENDING, RECEIVED, STARTED, RETRY
            message = "Pending: in the task queue"

    except:
        state = "MISSING"
        message = "Task does not exist"

    return dict(
        status=state,
        complete=fraction_complete,
        message=message,
        task_id=task_id)


def get_complex_receipt_sort(first_master_ids=[]):
    """
    method used to sort receipt items,
    It's gotta be done somehow
    """
    def complex_receipt_sort(purchase):
        master_id = purchase.product.content.master_id
        code = purchase.product.content.code or None

        term_1 = "C" if code is None else "A" if (master_id in first_master_ids) else "B"
        term_2 = code or ""
        return term_1 + term_2 + str(master_id)

    return complex_receipt_sort
