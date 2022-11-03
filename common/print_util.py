import unicodedata
import os, shutil



class Printer:
    def __init__(self, space, float_figure=2):
#         self.ori_format =  "{:"+str(space)+"s}"
        
        self.ori_format =  "{}"
        self.float_figure_value = float_figure
        self.float_figure = "{:.0"+str(float_figure)+"f}"
        self.unit_figure = "{} ({})"
        self.figure_factor = 1
        self.max_size = space
        
    def title(self, task, unit,result_column = "Result Name", init_column = "File Name"):
        if unit == "%":
            self.figure_factor = 100
        
        s = self.ori_format + self.ori_format + self.unit_figure
        print_s = s.format(self.fill_str_with_space(init_column), self.fill_str_with_space(result_column),task,unit)
        
        if unit == "Correct/Wrong":
            self.float_figure = "{}"
        
        print(print_s)
        return print_s
        
    def line(self, org_file, result_file, figure):
        s = self.ori_format + self.ori_format + self.float_figure 
        print_s = s.format(self.fill_str_with_space(org_file), self.fill_str_with_space(result_file), figure*self.figure_factor)
        print(print_s)
        return print_s
    
    def result(self, task, unit, total_file_count, figure, final_statement = "Total Image Count"):
        if self.float_figure == "{}":
            self.float_figure = "{:.0"+str(self.float_figure_value)+"f}"
        if unit == "%":
            self.figure_factor = 100
        s = self.ori_format + self.unit_figure + "\n" + self.ori_format + self.float_figure
        print_s = s.format(self.fill_str_with_space(final_statement), task, unit, self.fill_str_with_space(str(total_file_count)), figure*self.figure_factor)
        print(print_s)
        return print_s
    
    def fill_str_with_space(self, input_s, fill_char=" "):
        l = 0 
        for c in input_s:
#             print(unicodedata.east_asian_width(c))
#             if c in ['F', 'W']:
#                 l+=2
#             else: 
            l+=1
        return input_s+fill_char*int(((self.max_size/3)-l))
    
    def inout_print(self, input_dir, output_dir):
        s = self.ori_format + self.ori_format + "\n" + self.ori_format + self.ori_format
        print_s = s.format(self.fill_str_with_space("source directory:"), input_dir, self.fill_str_with_space("output directory:"), output_dir)
        print(print_s)
        return print_s
    
def reset_output(output_dir):
    if os.path.isdir(output_dir):
        shutil.rmtree(output_dir)
        os.mkdir(output_dir)
    else:
        os.mkdir(output_dir)