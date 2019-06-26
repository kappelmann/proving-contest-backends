import logging
import sys
import re
import codecs
import subprocess

from poller import Poller, Grader_Panic

pollurl = "pollsubmission/?itp=LEA"
puturl = "putresult/"
grader_path = "/var/lib/lean-grader/"
lean_compile_and_check = ["./grader.sh"]
axiom_re = re.compile("axiom ([^ ]*) .*")


class Poller_Lean(Poller):

    def init(self):
        self.make_pollurl("LEA")

    def grade_submission(self, submission_id, assessment_id, defs, submission, check, image, version, timeout_socket, timeout_all, allow_sorry, check_file):
        global grader_path, lean_compile_and_check, axiom_re
        logger = self.logger
        logger.debug("Copy Lean files")

        for name, content in (("Defs", defs), ("Submission", submission), ("Check", check)):
            logger.debug("writing file '{}{}.lean'!".format(grader_path, name))
            text_file = codecs.open(grader_path + name + ".lean", "w", "utf-8")
            text_file.write(content)
            text_file.close()

        logger.info("Compile & Check Lean proof output in container")

        returncode = -1
        error = None
        process = subprocess.Popen(
            lean_compile_and_check, stdout=subprocess.PIPE)
        try:
            output, error = process.communicate(timeout=timeout_all)
            timedout = False
            returncode = process.returncode
        except subprocess.TimeoutExpired:
            timedout = True

        if returncode == 4:
            # successfully checked
            grader_msg = "OK"
            result = "1"
        else:
            # error occurred or wrong, compose some grader message
            if timedout:
                grader_msg = "Lean Checking timed out (outer)"
            elif returncode == 5:
                grader_msg = "Compiling failed, message =\n{}".format(
                    "" if output is None else str(output))
            else:
                grader_msg = "Something went wrong. Here is some output\n{}".format(
                    "" if output is None else str(output))
            result = "0"

        return result, error, [grader_msg]

    def tidy(self):
        pass


if __name__ == "__main__":
    loglevel = logging.INFO
    if len(sys.argv) > 1:
        if sys.argv[1] == "DEBUG":
            loglevel = logging.DEBUG

    # Initialize logging
    logging.basicConfig(filename="poller.log",
                        filemode='a',
                        format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                        datefmt='%m-%d %H:%M:%S',
                        level=loglevel)

    Poller_Lean().run()
