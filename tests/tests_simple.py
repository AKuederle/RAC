import unittest
import unittest.mock as mock
import os
import sys
from copy import deepcopy
os.chdir(os.path.dirname(__file__))
sys.path.insert(0, os.path.abspath('..'))

import wolo.helper as helper


class TestHelperFunctions(unittest.TestCase):

    def test_pretty_print_index(self):
        test_index = (1, 4, "p3", 3)
        exspected_output = "[1][4][p3][3]"
        output = helper.pretty_print_index(test_index)
        self.assertEqual(output, exspected_output)

    def test_cut_or_pad_without_master_longer(self):
        test_master = range(0, 5)
        test_slave = test_master[:-2]
        exspected_output = [(0, 0), (1, 1), (2, 2), (3, None), (4, None)]
        output = list(helper.cut_or_pad(test_master, test_slave))
        self.assertEqual(exspected_output, output)

    def test_cut_or_pad_without_master_shorter(self):
        test_slave = range(0, 5)
        test_master = test_slave[:-2]
        exspected_output = [(0, 0), (1, 1), (2, 2)]
        output = list(helper.cut_or_pad(test_master, test_slave))
        self.assertEqual(exspected_output, output)

    def test_cut_or_pad_without_enum(self):
        test_master = test_slave = range(1, 4)
        exspected_output = [(0, 1, 1), (1, 2, 2), (2, 3, 3)]
        output = list(helper.cut_or_pad(test_master, test_slave, enum=True))
        self.assertEqual(exspected_output, output)

import wolo.parameters as parameters
import hashlib
from pathlib import Path
class TestParamterDefinitions(unittest.TestCase):

    def test_simple_parameter(self):
        test_parameter = parameters.Parameter("test", 4)
        exspected_log_value = 4
        self.assertEqual(test_parameter._log_value, exspected_log_value)

    def test_simple_parameter_manual_log_value(self):
        test_parameter = parameters.Parameter("test", 4, 5)
        exspected_log_value = 5
        self.assertEqual(test_parameter._log_value, exspected_log_value)

    @mock.patch("wolo.parameters.Path.is_file", side_effect=lambda: True)
    @mock.patch("wolo.parameters.Path.stat")
    def test_file_parameter(self, getmtime_mock, isfile_mock):
        type(getmtime_mock.return_value).st_mtime = mock.PropertyMock(return_value=11111)
        test_file = parameters.File("test", "../test_dir/test")
        self.assertEqual(test_file.name, "test")
        self.assertEqual(test_file.value, str(Path("../test_dir/test")))
        self.assertEqual(test_file._log_value, [str(Path("../test_dir/test")), 11111])

    @mock.patch("wolo.parameters.Path.is_file", side_effect=lambda: True)
    @mock.patch("wolo.parameters.Path.stat")
    def test_file_parameter_changed(self, getmtime_mock, isfile_mock):
        type(getmtime_mock.return_value).st_mtime = mock.PropertyMock(return_value=11111)
        test_file = parameters.File("test", "../test_dir/test")
        type(getmtime_mock.return_value).st_mtime = mock.PropertyMock(return_value=22222)
        self.assertEqual(test_file._get_mod_date(), 22222)
        self.assertTrue(test_file.changed())

    @mock.patch("wolo.parameters.Path.is_file", side_effect=lambda: False)
    @mock.patch("wolo.parameters.Path.stat")
    @mock.patch("wolo.parameters.Path.mkdir")
    @mock.patch("wolo.parameters.Path.open")
    def test_file_parameter_autocreate(self, open_mock, makedirs_mock, getmtime_mock, isfile_mock):
        getmtime_mock.st_mtime = 11111
        test_file = parameters.File("test", "../test_dir/test", autocreate=True)
        self.assertTrue(makedirs_mock.called)
        self.assertTrue(open_mock.called)

    @mock.patch("wolo.parameters.inspect.getsource", side_effect=lambda x: x)
    def test_source_parameter(self, getsource_mock):
        test_object = parameters.Source("this is a test")
        getsource_mock.assert_called_with("this is a test")
        self.assertEqual(test_object.name, "this is a test")
        self.assertEqual(test_object._log_value, hashlib.md5("this is a test".encode('utf-8')).hexdigest())

    @mock.patch("wolo.parameters.inspect.getsource", side_effect=lambda x: x)
    def test_source_parameter_changed(self, getsource_mock):
        test_object = parameters.Source("this is a test")
        getsource_mock.side_effect = lambda x: "this is changed test"
        self.assertTrue(test_object.changed())

    @mock.patch("wolo.parameters.Source.__init__")
    def test_self_paramter(self, source_mock):
        test_object = parameters.Self(list())
        source_mock.assert_called_with(object=list, name="Self")


import wolo.workflow as workflow

class ExampleWorkflow(workflow.Workflow):
    def tasktree(self):
        pass

class MockTask():
    def __init__(self, success, name):
        self.success = success
        self.name = name
    def _run(self, x):
        return helper.TaskLog(task_class=self.name, inputs={}, outputs={}, last_run_success=self.success)


class TestWorkflow(unittest.TestCase):
    maxDiff = None
    @mock.patch("wolo.workflow.Workflow._read_log")
    @mock.patch("wolo.workflow.Workflow._create_logfile")
    @mock.patch("wolo.workflow.Workflow.before")
    def test_workflow_init(self, before_mock, create_mock, readlog_mock):
        test_workflow = ExampleWorkflow(name="test")
        self.assertEqual(test_workflow._name, "ExampleWorkflow_test")
        self.assertTrue(before_mock.called)
        self.assertTrue(create_mock.called)

    def test_run_tasks_linear_empty_log(self):
        tree = []
        tree.append(MockTask(True, "0"))
        tree.append(MockTask(True, "1"))
        tree.append(MockTask(True, "2"))
        tree.append(MockTask(True, "3"))
        output = []
        output.append(helper.TaskLog(task_class="0", inputs={}, outputs={}, last_run_success=True))
        output.append(helper.TaskLog(task_class="1", inputs={}, outputs={}, last_run_success=True))
        output.append(helper.TaskLog(task_class="2", inputs={}, outputs={}, last_run_success=True))
        output.append(helper.TaskLog(task_class="3", inputs={}, outputs={}, last_run_success=True))
        success, log = workflow._run_tasks(tree, None)
        self.assertEqual(success, True)
        self.assertEqual(log, output)

    def test_run_tasks_linear_empty_log_fail(self):
        tree = []
        tree.append(MockTask(True, "0"))
        tree.append(MockTask(True, "1"))
        tree.append(MockTask(False, "2"))
        tree.append(MockTask(True, "3"))
        output = []
        output.append(helper.TaskLog(task_class="0", inputs={}, outputs={}, last_run_success=True))
        output.append(helper.TaskLog(task_class="1", inputs={}, outputs={}, last_run_success=True))
        output.append(helper.TaskLog(task_class="2", inputs={}, outputs={}, last_run_success=False))
        success, log = workflow._run_tasks(tree, None)
        self.assertEqual(success, False)
        self.assertEqual(log, output)

    def test_run_tasks_parallel_tasks_empty_log(self):
        tree = []
        tree.append(MockTask(True, "0"))
        tree.append([MockTask(True, "1_0"), MockTask(True, "1_1")])
        tree.append(MockTask(True, "2"))
        output = []
        output.append(helper.TaskLog(task_class="0", inputs={}, outputs={}, last_run_success=True))
        sublist = []
        sublist.append(helper.TaskLog(task_class="1_0", inputs={}, outputs={}, last_run_success=True))
        sublist.append(helper.TaskLog(task_class="1_1", inputs={}, outputs={}, last_run_success=True))
        output.append(sublist)
        output.append(helper.TaskLog(task_class="2", inputs={}, outputs={}, last_run_success=True))
        success, log = workflow._run_tasks(tree, None)
        self.assertEqual(success, True)
        self.assertEqual(log, output)

    def test_run_tasks_parallel_tasks_empty_log_fail(self):
        tree = []
        tree.append(MockTask(True, "0"))
        tree.append([MockTask(True, "1_0"), MockTask(False, "1_1")])
        tree.append(MockTask(True, "2"))
        output = []
        output.append(helper.TaskLog(task_class="0", inputs={}, outputs={}, last_run_success=True))
        sublist = []
        sublist.append(helper.TaskLog(task_class="1_0", inputs={}, outputs={}, last_run_success=True))
        sublist.append(helper.TaskLog(task_class="1_1", inputs={}, outputs={}, last_run_success=False))
        output.append(sublist)
        success, log = workflow._run_tasks(tree, None)
        self.assertEqual(success, False)
        self.assertEqual(log, output)

    def test_run_tasks_parallel_lists_empty_log(self):
        tree = []
        tree.append(MockTask(True, "0"))
        sublist1 = [MockTask(True, "1_0_0"), MockTask(True, "1_0_1")]
        sublist2 = [MockTask(True, "1_1_0"), MockTask(True, "1_1_1")]
        tree.append([sublist1, sublist2])
        tree.append(MockTask(True, "2"))
        output = []
        output.append(helper.TaskLog(task_class="0", inputs={}, outputs={}, last_run_success=True))
        sublog1 = []
        sublog1.append(helper.TaskLog(task_class="1_0_0", inputs={}, outputs={}, last_run_success=True))
        sublog1.append(helper.TaskLog(task_class="1_0_1", inputs={}, outputs={}, last_run_success=True))
        sublog2 = []
        sublog2.append(helper.TaskLog(task_class="1_1_0", inputs={}, outputs={}, last_run_success=True))
        sublog2.append(helper.TaskLog(task_class="1_1_1", inputs={}, outputs={}, last_run_success=True))
        output.append([sublog1, sublog2])
        output.append(helper.TaskLog(task_class="2", inputs={}, outputs={}, last_run_success=True))
        success, log = workflow._run_tasks(tree, None)
        self.assertEqual(success, True)
        self.assertEqual(log, output)

    def test_run_tasks_parallel_lists_empty_log_fail(self):
        tree = []
        tree.append(MockTask(True, "0"))
        sublist1 = [MockTask(True, "1_0_0"), MockTask(False, "1_0_1")]
        sublist2 = [MockTask(False, "1_1_0"), MockTask(True, "1_1_1")]
        tree.append([sublist1, sublist2])
        tree.append(MockTask(True, "2"))
        output = []
        output.append(helper.TaskLog(task_class="0", inputs={}, outputs={}, last_run_success=True))
        sublog1 = []
        sublog1.append(helper.TaskLog(task_class="1_0_0", inputs={}, outputs={}, last_run_success=True))
        sublog1.append(helper.TaskLog(task_class="1_0_1", inputs={}, outputs={}, last_run_success=False))
        sublog2 = []
        sublog2.append(helper.TaskLog(task_class="1_1_0", inputs={}, outputs={}, last_run_success=False))
        output.append([sublog1, sublog2])
        success, log = workflow._run_tasks(tree, None)
        self.assertEqual(success, False)
        self.assertEqual(log, output)

    def test_run_tasks_linear_log(self):
        tree = []
        tree.append(MockTask(True, "0"))
        tree.append(MockTask(True, "1"))
        tree.append(MockTask(True, "2"))
        tree.append(MockTask(True, "3"))
        in_log = []
        in_log.append(helper.TaskLog(task_class="0", inputs={}, outputs={}, last_run_success=True))
        in_log.append(helper.TaskLog(task_class="1", inputs={}, outputs={}, last_run_success=True))
        in_log.append(helper.TaskLog(task_class="2", inputs={}, outputs={}, last_run_success=True))
        in_log.append(helper.TaskLog(task_class="3", inputs={}, outputs={}, last_run_success=True))
        out_log = deepcopy(in_log)
        success, log = workflow._run_tasks(tree, in_log)
        self.assertEqual(success, True)
        self.assertEqual(log, out_log)

    def test_run_tasks_linear_log_fail(self):
        tree = []
        tree.append(MockTask(True, "0"))
        tree.append(MockTask(True, "1"))
        tree.append(MockTask(False, "2"))
        tree.append(MockTask(True, "3"))
        in_log = []
        in_log.append(helper.TaskLog(task_class="0", inputs={}, outputs={}, last_run_success=True))
        in_log.append(helper.TaskLog(task_class="1", inputs={}, outputs={}, last_run_success=True))
        in_log.append(helper.TaskLog(task_class="2", inputs={}, outputs={}, last_run_success=True))
        in_log.append(helper.TaskLog(task_class="3", inputs={}, outputs={}, last_run_success=True))
        out_log = deepcopy(in_log)
        out_log[2] = helper.TaskLog(task_class="2", inputs={}, outputs={}, last_run_success=False)
        success, log = workflow._run_tasks(tree, in_log)
        self.assertEqual(success, False)
        self.assertEqual(log, out_log)

    def test_run_tasks_parallel_tasks_log(self):
        tree = []
        tree.append(MockTask(True, "0"))
        tree.append([MockTask(True, "1_0"), MockTask(True, "1_1")])
        tree.append(MockTask(True, "2"))
        in_log = []
        in_log.append(helper.TaskLog(task_class="0", inputs={}, outputs={}, last_run_success=True))
        sublist = []
        sublist.append(helper.TaskLog(task_class="1_0", inputs={}, outputs={}, last_run_success=True))
        sublist.append(helper.TaskLog(task_class="1_1", inputs={}, outputs={}, last_run_success=True))
        in_log.append(sublist)
        in_log.append(helper.TaskLog(task_class="2", inputs={}, outputs={}, last_run_success=True))
        out_log = deepcopy(in_log)
        success, log = workflow._run_tasks(tree, in_log)
        self.assertEqual(success, True)
        self.assertEqual(log, out_log)

    def test_run_tasks_parallel_tasks_log_fail(self):
        tree = []
        tree.append(MockTask(True, "0"))
        tree.append([MockTask(True, "1_0"), MockTask(False, "1_1")])
        tree.append(MockTask(True, "2"))
        in_log = []
        in_log.append(helper.TaskLog(task_class="0", inputs={}, outputs={}, last_run_success=True))
        sublist = []
        sublist.append(helper.TaskLog(task_class="1_0", inputs={}, outputs={}, last_run_success=True))
        sublist.append(helper.TaskLog(task_class="1_1", inputs={}, outputs={}, last_run_success=True))
        in_log.append(sublist)
        in_log.append(helper.TaskLog(task_class="2", inputs={}, outputs={}, last_run_success=True))
        out_log = deepcopy(in_log)
        out_log[1][1] = helper.TaskLog(task_class="1_1", inputs={}, outputs={}, last_run_success=False)
        success, log = workflow._run_tasks(tree, in_log)
        self.assertEqual(success, False)
        self.assertEqual(log, out_log)

    def test_run_tasks_parallel_lists_log(self):
        tree = []
        tree.append(MockTask(True, "0"))
        sublist1 = [MockTask(True, "1_0_0"), MockTask(True, "1_0_1")]
        sublist2 = [MockTask(True, "1_1_0"), MockTask(True, "1_1_1")]
        tree.append([sublist1, sublist2])
        tree.append(MockTask(True, "2"))
        in_log = []
        in_log.append(helper.TaskLog(task_class="0", inputs={}, outputs={}, last_run_success=True))
        sublog1 = []
        sublog1.append(helper.TaskLog(task_class="1_0_0", inputs={}, outputs={}, last_run_success=True))
        sublog1.append(helper.TaskLog(task_class="1_0_1", inputs={}, outputs={}, last_run_success=True))
        sublog2 = []
        sublog2.append(helper.TaskLog(task_class="1_1_0", inputs={}, outputs={}, last_run_success=True))
        sublog2.append(helper.TaskLog(task_class="1_1_1", inputs={}, outputs={}, last_run_success=True))
        in_log.append([sublog1, sublog2])
        in_log.append(helper.TaskLog(task_class="2", inputs={}, outputs={}, last_run_success=True))
        out_log = deepcopy(in_log)
        success, log = workflow._run_tasks(tree, in_log)
        self.assertEqual(success, True)
        self.assertEqual(log, out_log)

    def test_run_tasks_parallel_lists_log_fail(self):
        tree = []
        tree.append(MockTask(True, "0"))
        sublist1 = [MockTask(True, "1_0_0"), MockTask(False, "1_0_1")]
        sublist2 = [MockTask(False, "1_1_0"), MockTask(True, "1_1_1")]
        tree.append([sublist1, sublist2])
        tree.append(MockTask(True, "2"))
        in_log = []
        in_log.append(helper.TaskLog(task_class="0", inputs={}, outputs={}, last_run_success=True))
        sublog1 = []
        sublog1.append(helper.TaskLog(task_class="1_0_0", inputs={}, outputs={}, last_run_success=True))
        sublog1.append(helper.TaskLog(task_class="1_0_1", inputs={}, outputs={}, last_run_success=True))
        sublog2 = []
        sublog2.append(helper.TaskLog(task_class="1_1_0", inputs={}, outputs={}, last_run_success=True))
        sublog2.append(helper.TaskLog(task_class="1_1_1", inputs={}, outputs={}, last_run_success=True))
        in_log.append([sublog1, sublog2])
        in_log.append(helper.TaskLog(task_class="2", inputs={}, outputs={}, last_run_success=True))
        out_log = deepcopy(in_log)
        out_log[1][0][1] = helper.TaskLog(task_class="1_0_1", inputs={}, outputs={}, last_run_success=False)
        out_log[1][1][0] = helper.TaskLog(task_class="1_1_0", inputs={}, outputs={}, last_run_success=False)
        success, log = workflow._run_tasks(tree, in_log)
        self.assertEqual(success, False)
        self.assertEqual(log, out_log)

    def test_run_tasks_parallel_tasks_wrong_log(self):
        tree = []
        tree.append(MockTask(True, "0"))
        tree.append([MockTask(True, "1_0"), MockTask(True, "1_1")])
        tree.append(MockTask(True, "2"))
        in_log = []
        in_log.append(helper.TaskLog(task_class="0", inputs={}, outputs={}, last_run_success=True))
        in_log.append(helper.TaskLog(task_class="1", inputs={}, outputs={}, last_run_success=True))
        in_log.append(helper.TaskLog(task_class="2", inputs={}, outputs={}, last_run_success=True))
        out_log = deepcopy(in_log)
        sublist = []
        sublist.append(helper.TaskLog(task_class="1_0", inputs={}, outputs={}, last_run_success=True))
        sublist.append(helper.TaskLog(task_class="1_1", inputs={}, outputs={}, last_run_success=True))
        out_log[1] = sublist
        success, log = workflow._run_tasks(tree, in_log)
        self.assertEqual(success, True)
        self.assertEqual(log, out_log)

    def test_run_tasks_parallel_tasks_crop_log(self):
        tree = []
        tree.append(MockTask(True, "0"))
        tree.append(MockTask(True, "1"))
        tree.append(MockTask(True, "2"))
        in_log = []
        in_log.append(helper.TaskLog(task_class="0", inputs={}, outputs={}, last_run_success=True))
        in_log.append(helper.TaskLog(task_class="1", inputs={}, outputs={}, last_run_success=True))
        in_log.append(helper.TaskLog(task_class="2", inputs={}, outputs={}, last_run_success=True))
        in_log.append(helper.TaskLog(task_class="3", inputs={}, outputs={}, last_run_success=True))
        out_log = deepcopy(in_log)
        del out_log[-1]
        success, log = workflow._run_tasks(tree, in_log)
        self.assertEqual(success, True)
        self.assertEqual(log, out_log)

    def test_run_tasks_inherent_fail(self):
        tree = []
        tree.append(MockTask(True, "0"))
        tree.append(MockTask(False, "1"))
        tree.append(MockTask(False, "2"))
        tree.append(MockTask(True, "3"))
        in_log = []
        in_log.append(helper.TaskLog(task_class="0", inputs={}, outputs={}, last_run_success=True))
        in_log.append(helper.TaskLog(task_class="1", inputs={}, outputs={}, last_run_success=True))
        in_log.append(helper.TaskLog(task_class="2", inputs={}, outputs={}, last_run_success=True))
        in_log.append(helper.TaskLog(task_class="3", inputs={}, outputs={}, last_run_success=True))
        out_log = deepcopy(in_log)
        out_log[1] = helper.TaskLog(task_class="1", inputs={}, outputs={}, last_run_success=False)
        success, log = workflow._run_tasks(tree, in_log)
        self.assertEqual(success, False)
        self.assertEqual(log, out_log)

















if __name__ == '__main__':
    unittest.main(buffer=True)
