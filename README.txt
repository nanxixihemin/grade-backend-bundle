
运行顺序（Windows / macOS 都一样）：

1. 安装依赖
   pip install -r requirements.txt

2. 导入课程
   python seed_from_excel.py

3. 启动后端
   python app.py

4. 浏览器打开
   http://127.0.0.1:5000

说明：
- UI 保持不变，已经接上后端。
- 成绩输入后会写入 grades.db。
- 刷新页面不会丢。
- 换设备使用时，只要部署这个项目到服务器即可。
