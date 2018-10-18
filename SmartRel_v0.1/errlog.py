from os import listdir, stat, getcwd, remove

class ErrorLog:
    # log saved on ESP as a file
    def __init__(self, log_filename=None, time_stamp=1, screen_output=1):

        self.time_stamp_in_log = time_stamp
        self.valid_logfile = False
        self.output2screen = screen_output

        if log_filename is None:
            self.err_log = getcwd() + 'HPi_err.log'
        else:
            self.err_log = log_filename

        self.check_logfile_valid()

    def check_logfile_valid(self):
        # verify existance of log file
        if self.err_log in listdir():
            self.valid_logfile = True
        # create new file
        else:
            open(self.err_log, 'a').close()

            if self.err_log in listdir():
                self.valid_logfile = True

            if self.valid_logfile is True:
                msg = '>>Log file %s was created successfully' % self.err_log
            else:
                msg = '>>Log file %s failed to create' % self.err_log

            self.append_log(msg, time_stamp=1)

    def append_log(self, log_entry='', time_stamp=None):
        # permanent time_stamp
        if time_stamp is None:
            if self.time_stamp_in_log == 1:
                self.msg = '%s %s' % (self.time_stamp(), log_entry)
            else:
                self.msg = '%s' % log_entry
        # ADHOC time_stamp - over-rides permanent one
        elif time_stamp is 1:
            self.msg = '%s %s' % (self.time_stamp(), log_entry)
        elif time_stamp is 0:
            self.msg = '%s' % log_entry

        if self.valid_logfile is True:
            myfile = open(self.err_log, 'a')
            myfile.write(self.msg + '\n')
            myfile.close()
        else:
            print('Log err')

        if self.output2screen == 1:
            print(self.msg)

        # if stat(self.err_log)[6] > 1000:
        #     self.pub("error_log file exceeds its allowed size")
        # if stat(self.err_log)[6] > 5000:
        #     self.pub("error_log file deleted")
        #     os.remove(self.err_log)

    def xport_logfile(self):
        # return listdir()
        if self.err_log in listdir() is True:
            with open(self.err_log, 'r') as f:
                return f.readlines()
        else:
            print('file', self.err_log, ' not found')
            return 0

