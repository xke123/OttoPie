import sys
import os
import importlib.util
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QSpinBox, QTextEdit, QFileDialog,
    QDialog, QDialogButtonBox, QTabWidget, QMessageBox, QGroupBox
)
from PyQt5.QtCore import QTimer, Qt, pyqtSignal, QObject

# ===============================
# 对话框：任务脚本配置编辑
# ===============================
class ScriptConfigDialog(QDialog):
    def __init__(self, config=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("配置任务脚本")
        self.resize(400, 220)
        self.config = config if config else {}

        layout = QVBoxLayout()

        # 脚本文件
        script_layout = QHBoxLayout()
        self.script_label = QLabel("脚本文件:")
        self.script_line = QLineEdit()
        self.script_btn = QPushButton("选择文件")
        self.script_btn.clicked.connect(self.choose_script)
        script_layout.addWidget(self.script_label)
        script_layout.addWidget(self.script_line)
        script_layout.addWidget(self.script_btn)
        layout.addLayout(script_layout)

        # 源文件夹
        src_layout = QHBoxLayout()
        self.src_label = QLabel("源文件夹:")
        self.src_line = QLineEdit()
        self.src_btn = QPushButton("选择文件夹")
        self.src_btn.clicked.connect(self.choose_src)
        src_layout.addWidget(self.src_label)
        src_layout.addWidget(self.src_line)
        src_layout.addWidget(self.src_btn)
        layout.addLayout(src_layout)

        # 目标文件夹
        tgt_layout = QHBoxLayout()
        self.tgt_label = QLabel("目标文件夹:")
        self.tgt_line = QLineEdit()
        self.tgt_btn = QPushButton("选择文件夹")
        self.tgt_btn.clicked.connect(self.choose_tgt)
        tgt_layout.addWidget(self.tgt_label)
        tgt_layout.addWidget(self.tgt_line)
        tgt_layout.addWidget(self.tgt_btn)
        layout.addLayout(tgt_layout)

        # 执行间隔
        interval_layout = QHBoxLayout()
        self.interval_label = QLabel("执行间隔 (秒):")
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(1, 3600)
        interval_layout.addWidget(self.interval_label)
        interval_layout.addWidget(self.interval_spin)
        layout.addLayout(interval_layout)

        # 对话框按钮
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        layout.addWidget(self.buttonBox)

        self.setLayout(layout)
        self.load_config()

    def load_config(self):
        # 如果已有配置，则填充各个字段
        self.script_line.setText(self.config.get("script_path", ""))
        self.src_line.setText(self.config.get("src", ""))
        self.tgt_line.setText(self.config.get("tgt", ""))
        self.interval_spin.setValue(self.config.get("interval", 10))

    def choose_script(self):
        filename, _ = QFileDialog.getOpenFileName(self, "选择任务脚本", "", "Python Files (*.py)")
        if filename:
            self.script_line.setText(filename)

    def choose_src(self):
        folder = QFileDialog.getExistingDirectory(self, "选择源文件夹")
        if folder:
            self.src_line.setText(folder)

    def choose_tgt(self):
        folder = QFileDialog.getExistingDirectory(self, "选择目标文件夹")
        if folder:
            self.tgt_line.setText(folder)

    def get_config(self):
        # 返回配置字典
        return {
            "script_path": self.script_line.text().strip(),
            "src": self.src_line.text().strip(),
            "tgt": self.tgt_line.text().strip(),
            "interval": self.interval_spin.value()
        }

# ===============================
# 任务项：封装每个脚本任务
# ===============================
class TaskWidget(QWidget):
    log_signal = pyqtSignal(str)  # 用于向主窗体发送日志信息
    removed_signal = pyqtSignal(object)  # 用于通知删除任务

    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self.script_module = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.run_task)
        self.running = False
        self.load_script_module()

        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout()

        # 显示脚本文件名称
        self.label = QLabel(os.path.basename(self.config.get("script_path", "")))
        layout.addWidget(self.label)

        # 启动/停止按钮
        self.start_stop_btn = QPushButton("启动")
        self.start_stop_btn.clicked.connect(self.toggle_running)
        layout.addWidget(self.start_stop_btn)

        # 编辑配置按钮
        self.edit_btn = QPushButton("编辑配置")
        self.edit_btn.clicked.connect(self.edit_config)
        layout.addWidget(self.edit_btn)

        # 删除按钮
        self.del_btn = QPushButton("删除")
        self.del_btn.clicked.connect(self.delete_self)
        layout.addWidget(self.del_btn)

        self.setLayout(layout)

    def load_script_module(self):
        """动态加载脚本模块，并检查是否有 run() 接口"""
        path = self.config.get("script_path", "")
        if not path:
            self.log("脚本路径为空")
            return
        module_name = "task_plugin_" + os.path.basename(path).replace(".", "_")
        spec = importlib.util.spec_from_file_location(module_name, path)
        module = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(module)
            if hasattr(module, "run"):
                self.script_module = module
                self.log("加载脚本成功: " + path)
            else:
                self.log("加载失败，脚本中未定义 run(params)")
                self.script_module = None
        except Exception as e:
            self.log("加载脚本异常: " + str(e))
            self.script_module = None

    def toggle_running(self):
        if self.running:
            self.stop()
        else:
            self.start()

    def start(self):
        if not self.script_module:
            self.log("脚本模块未加载，无法启动")
            return
        interval = self.config.get("interval", 10) * 1000
        self.timer.start(interval)
        self.running = True
        self.start_stop_btn.setText("停止")
        self.log("任务启动，间隔 {} 秒".format(self.config.get("interval", 10)))

    def stop(self):
        self.timer.stop()
        self.running = False
        self.start_stop_btn.setText("启动")
        self.log("任务停止")

    def edit_config(self):
        # 修改配置前先停止任务
        if self.running:
            self.stop()
        dialog = ScriptConfigDialog(self.config, self)
        if dialog.exec_() == QDialog.Accepted:
            new_config = dialog.get_config()
            self.config = new_config
            # 重新加载脚本模块
            self.load_script_module()
            # 如果需要自动重启任务，则在此处调用 self.start()
            self.log("配置已修改")
        else:
            self.log("取消配置修改")

    def delete_self(self):
        self.stop()
        self.log("任务删除")
        # 发出信号通知主界面删除该任务项
        self.removed_signal.emit(self)

    def run_task(self):
    # 如果任务正在执行，则跳过本次调用
        if getattr(self, "is_executing", False):
            self.log("上次任务尚未完成，本次执行已跳过")
            return

        self.is_executing = True  # 标记任务开始执行
        try:
            if not self.script_module:
                self.log("脚本模块未加载，任务无法执行")
                return
            params = {
                "src": self.config.get("src", ""),
                "tgt": self.config.get("tgt", "")
            }
            result = self.script_module.run(params)
            self.log("任务执行结果: " + str(result))
        except Exception as e:
            self.log("任务执行异常: " + str(e))
        finally:
            # 任务执行完毕，重置标志
            self.is_executing = False


    def log(self, message):
        msg = "[{}] {}".format(os.path.basename(self.config.get("script_path", "")), message)
        self.log_signal.emit(msg)

# ===============================
# 主窗口：包含脚本管理和任务日志两个Tab
# ===============================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("自动化任务平台")
        self.resize(700, 500)
        self.task_widgets = []  # 存储所有任务项

        self.init_ui()

    def init_ui(self):
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # 脚本管理页
        self.manage_tab = QWidget()
        self.manage_layout = QVBoxLayout()
        # “添加任务”按钮
        self.add_task_btn = QPushButton("添加任务")
        self.add_task_btn.clicked.connect(self.add_task)
        self.manage_layout.addWidget(self.add_task_btn)

        # 用于存放任务项的区域
        self.task_list_widget = QWidget()
        self.task_list_layout = QVBoxLayout()
        self.task_list_layout.setAlignment(Qt.AlignTop)
        self.task_list_widget.setLayout(self.task_list_layout)
        self.manage_layout.addWidget(self.task_list_widget)
        self.manage_tab.setLayout(self.manage_layout)

        # 任务日志页
        self.log_tab = QWidget()
        self.log_layout = QVBoxLayout()
        self.log_edit = QTextEdit()
        self.log_edit.setReadOnly(True)
        self.log_layout.addWidget(self.log_edit)
        self.log_tab.setLayout(self.log_layout)

        self.tabs.addTab(self.manage_tab, "脚本管理")
        self.tabs.addTab(self.log_tab, "任务日志")

    def add_task(self):
        dialog = ScriptConfigDialog(parent=self)
        if dialog.exec_() == QDialog.Accepted:
            config = dialog.get_config()
            # 检查必要的配置
            if not config.get("script_path"):
                QMessageBox.warning(self, "配置错误", "请指定脚本文件")
                return
            task_widget = TaskWidget(config, self)
            task_widget.log_signal.connect(self.append_log)
            task_widget.removed_signal.connect(self.remove_task)
            self.task_widgets.append(task_widget)
            # 用 QGroupBox 包裹任务项，便于显示标题
            group = QGroupBox(os.path.basename(config.get("script_path")))
            group_layout = QVBoxLayout()
            group_layout.addWidget(task_widget)
            group.setLayout(group_layout)
            # 将 group 存储为任务项的一个属性，方便后续删除
            task_widget.group_box = group
            self.task_list_layout.addWidget(group)
            self.append_log("添加任务：" + config.get("script_path"))
        else:
            self.append_log("添加任务已取消")

    def remove_task(self, task_widget):
        # 从布局和列表中删除任务项
        if task_widget in self.task_widgets:
            self.task_widgets.remove(task_widget)
            self.task_list_layout.removeWidget(task_widget.group_box)
            task_widget.group_box.deleteLater()
            self.append_log("删除任务：" + os.path.basename(task_widget.config.get("script_path", "")))

    def append_log(self, message):
        self.log_edit.append(message)

# ===============================
# 主程序入口
# ===============================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
