def get_task(self, task_time):
    task_time = {'start_days': [1, 2, 3], 'start_time': '19:00:00', 'end_days': [1, 2, 3], 'end_time': '20:00:00'}
    # if all(task_time['start_days']) < 6 and all(task_time['start_days']) > 0:
    #     pass
    # else:
    #     print("BAD DAYS FORMAT")
    #     quit()
    temp = task_time
    for i in range(len(task_time['start_days'])):
        m = len(self.all_tasks_sched)
        temp['task_num'] = '%d/%d' % ((m + 1), i)
        # t# emp['start_days'] = task_time['start_days'][i]
        # temp['end_days']=task_time['end_days'][i]

        print(temp)

    current_task_time = self.time2ticks(task_time)
    self.all_tasks_sched.append(current_task_time)