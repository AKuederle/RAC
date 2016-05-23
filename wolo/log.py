from pathlib import Path
import json

from .helper import pretty_print_index, convert_return


class TaskLog():
    def __init__(self, index, task_class, inputs={}, outputs={}, info={}, last_run_success=None):
        self.index = index
        self.task_class = task_class
        self.inputs = inputs
        self.outputs = outputs
        self.last_run_success = last_run_success
        self.info = info

    def __getitem__(self, selection):
        return {key: self.__dict__[key] for key in selection}

    def __iter__(self):
        for attr, value in self.__dict__.items():
            yield attr, value

    def __repr__(self):
        values = ", ".join(["{} = {}".format(key, value) for key, value in dict(self).items()])
        return "TaskLog({})".format(values)

    def __eq__(self, other):
        return (isinstance(other, self.__class__) and self.__dict__ == other.__dict__)

    def __ne__(self, other):
        return not self.__eq__(other)

    def _to_dict(self):
        i = pretty_print_index(self.index, style="underscore")
        value = dict(self)
        return i, value

    @classmethod
    def _from_dict(cls, dict):
        return cls(**dict)


class Log():
    """Wolo will create all the logs is a subfolder of the current working dir called .wolo.
    Be aware, that you have to call the workflow file from the same working directory every time
    """
    def __init__(self, name, log_dic=None):
        if log_dic:
            self._log_dic = Path(log_dic)
        else:
            self._log_dic = Path.cwd()
        self._log_dic = self._log_dic / ".wolo"
        self._log_path = self._log_dic / ".{}".format(name)
        self._log = None
        self._flattened = None

    @property
    def log(self):
        if not self._log:
            self._log = self._load()
        return self._log

    def _set_log(self, new_log):
        self._log = new_log
        self._write()

    @property
    def flat(self):
        """holds a flattended version of log. Can be used to further Dataanalysis. See FlatView() class for more details"""
        if not self._flattened:
            self._flattened = FlatView(self.log)
        return self._flattened

    def _load(self):
        if self._log_path.is_file():
            temp_log = json.load(self._log_path.open("r"))
            return list(_recursive_iterate_log(temp_log, TaskLog._from_dict))
        else:
            return []

    def _write(self):
        self._log_dic.mkdir(parents=True, exist_ok=True)
        save_log = _recursive_iterate_log(self.log, lambda x: dict(x))
        json.dump(list(save_log), self._log_path.open("w"), sort_keys=True, indent=4)

    def simple_tree(self, formatter=lambda x: x.task_class):
        return list(_recursive_iterate_log(self.log, formatter))


class FlatView():
    """FlatView is a flat Dictionary representation of a Log. The intendet usage is to select wanted columns and then exporting it for external Dataanalysis.
    The selectable columns using the .cols(selection) methode are:
    - "task_class": Class/Name of the task
    - "inputs": Dict containing all inputs
    - "outputs": Dict containing all outputs
    - "info": Dict containing addtional information returnend by the after method
    - "last_run_success": True or False depending if the last time the run was successful
    - "index": index in tuple form. A string representation of index is already used as main object identifier

    Note: The col methods still passes all the information to the new Object. So the col selection can be changed from the same Object.

    It is also possible to create a new column from a specific input or output using the .col_from_prop(prop, subprop) method using "inputs"
    or "outputs" as prop and the wanted parameter name as subprop.
    """

    def __init__(self, log, initial=None, flatten=True):
        if flatten is True:
            self.log = dict(_flatten_log(log))
        else:
            self.log = log
        if not initial:
            self._initial = self.log
        else:
            self._initial = initial

    def __repr__(self):
        return self.log

    def __str__(self):
        return str(self.log)

    def __iter__(self):
        for key, element in self.log.items():
            yield key, element

    def __getitem__(self, selection):
        new_log = self.log[selection]
        return FlatView(new_log, initial=self._initial, flatten=False)

    def cols(self, selection):
        """Take list of property name and return FlatView object whith just these columns"""
        selection = convert_return(selection)
        new_log = {key: {in_key: val[in_key] for in_key in selection} for key, val in self._initial.items()}
        return FlatView(new_log, initial=self._initial, flatten=False)

    def col_from_prop(self, prop, subprop, include_hash=False):
        for key, value in self._initial.items():
            if subprop in value[prop]:
                val = self.log[key]
                new_value = convert_return(value[prop][subprop])
                if include_hash is False:
                    new_value = new_value[0]
                val.update({"_".join([prop, subprop]): new_value})
                self.log[key] = val
        return FlatView(self.log, initial=self._initial, flatten=False)

    def to_pandas(self):
        import pandas as pd
        return pd.DataFrame.from_dict(self.log, orient="index")


def _flatten_log(L):
    """Flattens a nested log"""
    for i in L:
        if isinstance(i, TaskLog):
            yield i._to_dict()
        else:
            yield from _flatten_log(i)


def _recursive_iterate_log(L, func):
    for i in L:
        if isinstance(i, (list, tuple)):
            yield list(_recursive_iterate_log(i, func))
        else:
            yield func(i)
