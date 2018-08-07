import itertools
import math
import random
from functools import reduce


class ParamMutator(object):
    def __init__(self, vars):
        self.vars = vars
        self.max_var_values_number = self.calc_max_var_values_number(vars)

    def get_var(self, var_name):
        for v in self.vars:
            if v['name'] == var_name:
                return v
        raise KeyError(f'{var_name} not found')

    def calc_max_var_values_number(self, vars):
        mp = {}
        for var in vars:
            if var['plus_or_mult'] == 'plus':
                n = math.ceil((var['end'] - var['start']) / float(var['koef']))
            else:
                n = math.ceil(math.log(var['end'] / var['start']) / math.log(var['koef']))
            mp[var['name']] = n
        return mp

    def calc_all_comb_number(self, max_var_values_number):
        return reduce(lambda x, y: x * y, max_var_values_number.values())

    def get_n_values_for_each_variable(self, n_total, max_var_values_number):
        all_comb_number = self.calc_all_comb_number(self.max_var_values_number)
        ratio = (all_comb_number / n_total) ** (1.0 / len(self.max_var_values_number))

        mult = 1.
        rounded_mult = 1.
        res = {}
        for k, v in self.max_var_values_number.items():
            mult *= v / ratio
            if (abs(rounded_mult * math.ceil(mult / rounded_mult) - mult)
                    < abs(rounded_mult * math.floor(mult / rounded_mult) - mult)):
                adjusted_n = math.ceil(mult / rounded_mult)
            else:
                adjusted_n = math.floor(mult / rounded_mult)
                if adjusted_n == 0:
                    adjusted_n = 1
            rounded_mult *= adjusted_n
            res[k] = adjusted_n
        return res

    def mutate(self, n_vals, fraction_to_keep):
        if n_vals <= 0:
            raise ValueError(f'Invalid value: {n_vals}')
        n_vals_for_each_var = self.get_n_values_for_each_variable(n_vals * fraction_to_keep, self.max_var_values_number)
        points_for_each_var = self.get_points_for_each_var(self.max_var_values_number, n_vals_for_each_var)
        values_for_each_var = self.get_values_for_each_var(points_for_each_var)
        return values_for_each_var, self.generate_values(values_for_each_var, n_vals)

    def get_points_for_each_var(self, max_var_values_number, n_vals_for_each_var):
        res = {}
        import random
        for k, v in max_var_values_number.items():
            res[k] = sorted(random.sample(range(v), n_vals_for_each_var[k]))
        return res

    def generate_values(self, values_for_each_var, n_vals):
        values_for_each_var_list = [(k, v) for k, v in values_for_each_var.items()]
        vars, values = zip(*values_for_each_var_list)
        all_combinations = [element for element in itertools.product(*values)]
        return vars, random.sample(all_combinations, n_vals)

    def transform(self, k, points):
        values = []
        v = self.get_var(k)
        for point in points:
            if v['plus_or_mult'] == 'plus':
                values.append(v['start'] + v['koef'] * point)
            else:
                values.append(v['start'] * v['koef'] ** point)
        return values

    def get_values_for_each_var(self, points_for_each_var):
        return {k: self.transform(k, points) for k, points in points_for_each_var.items()}
