# Young_Module

Useful Codes for data parsing and printing



## Parser

Designed for txtfile recorded dataset

Parsing YOLO Datset

```bash
cd parser
python parser.py --type YOLO  --source path/to/source --save-dir where/to/save/files
```

Parsing YOLOP/Hybridnets Dataset

```bash
cd parser
python parser.py --type YOLOP --source path/to/source --save-dir where/to/save/files
```


## Printer

Designed for formatted result printing with even spacing

```python
from common.printer import Printer

printer = Printer(100, float_figure=4)
for _ in range(100):
  printer.line("input", "output", line_result)

printer.result(task, unit, total_file_count, figure, final_statement = "Total Image Count")

```
