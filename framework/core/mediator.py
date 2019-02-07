from framework.core.answer import Answer


class Mediator(object):

    def __init__(self, context, questioner, oracle):
        self.context = context
        self.questioner = questioner
        self.oracle = oracle

    def run(self, output_dir):
        iteration = 0

        while True:
            if iteration == 0:
                self.context.save_scores(output_dir, iteration)

            iteration += 1

            if iteration > len(self.context.code_element_set.code_elements):
                print("TOO MUCH ITERATIONS :( [%d]" % iteration)
                break

            subject = self.questioner.next_subject()
            print(subject)

            if subject.score == 0:
                print("ZERO :( [%d]" % iteration)
                break

            answer = self.oracle.ask_about(subject)
            print(answer)

            if answer == Answer.YES:
                print("EUREKA!!! [%d]" % iteration)
                break

            self.questioner.acknowledge(answer)

        self.context.save_scores(output_dir, iteration)
