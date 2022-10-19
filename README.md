## Environment:
python3
## Requirements:

- requests
- beautifulsoup4
- pycryptodome
- prettytable
- ddddocr
## Usage

```
pip install -r requirements.txt
```
- **手动指定**讲座序号，运行后通过命令行输入讲座编号(0,1,2,...)
```
python autolecture.py -u [yourIDcardNum] -p [yourPassword]  
```
- **自动指定**讲座序号，通过可选参数 -id [lectureNum] 传入(0,1,2...)
```
python autolecture.py -u [yourIDcardNum] -p [yourPassword] -id [lectureNum]
```
## Notice
- to add...


