from utils import make_a_log_file
import time


if __name__ == '__main__':
    log = make_a_log_file("http_monitoring.log")

    while True:
        log.info("")
        time.sleep(0.1)

    # with open("test.txt", 'r') as file_:
    #         # Go to the end of file
    #         file_.seek(0,2)
    #         while True:
    #             curr_position = file_.tell()
    #             line = file_.readline()
    #             if not line:
    #                 file_.seek(curr_position)
    #                 log.info(curr_position)
    #             else:
    #                 log.info("Line found \n")
    #                 log.info(line)
    #             time.sleep(1)