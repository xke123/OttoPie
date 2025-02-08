import sys
import os
import importlib.util
import json
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QSpinBox, QTextEdit, QFileDialog,
    QDialog, QDialogButtonBox, QTabWidget, QMessageBox, QGroupBox
)
from PyQt5.QtCore import QTimer, Qt, pyqtSignal

# 配置记录文件名称
CONFIG_RECORD_FILE = "tasks_config.json"

# ===============================
# 对话框：任务脚本配置编辑（修改版）
# ===============================
class ScriptConfigDialog(QDialog):
    def __init__(self, config=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("配置任务脚本")
        self.resize(500, 250)
        self.config = config if config else {}

        layout = QVBoxLayout()

        # 脚本文件选择
        script_layout = QHBoxLayout()
        self.script_label = QLabel("脚本文件:")
        self.script_line = QLineEdit()
        self.script_btn = QPushButton("选择文件")
        self.script_btn.clicked.connect(self.choose_script)
        script_layout.addWidget(self.script_label)
        script_layout.addWidget(self.script_line)
        script_layout.addWidget(self.script_btn)
        layout.addLayout(script_layout)

        # 源文件夹选择
        src_layout = QHBoxLayout()
        self.src_label = QLabel("源文件夹:")
        self.src_line = QLineEdit()
        self.src_btn = QPushButton("选择文件夹")
        self.src_btn.clicked.connect(self.choose_src)
        src_layout.addWidget(self.src_label)
        src_layout.addWidget(self.src_line)
        src_layout.addWidget(self.src_btn)
        layout.addLayout(src_layout)

        # 目标文件夹选择
        tgt_layout = QHBoxLayout()
        self.tgt_label = QLabel("目标文件夹:")
        self.tgt_line = QLineEdit()
        self.tgt_btn = QPushButton("选择文件夹")
        self.tgt_btn.clicked.connect(self.choose_tgt)
        tgt_layout.addWidget(self.tgt_label)
        tgt_layout.addWidget(self.tgt_line)
        tgt_layout.addWidget(self.tgt_btn)
        layout.addLayout(tgt_layout)

        # 执行间隔设置：增加天、小时、分钟、秒
        interval_layout = QHBoxLayout()
        interval_label = QLabel("执行间隔:")
        self.days_spin = QSpinBox()
        self.days_spin.setRange(0, 365)
        self.days_spin.setSuffix(" 天")
        self.hours_spin = QSpinBox()
        self.hours_spin.setRange(0, 23)
        self.hours_spin.setSuffix(" 小时")
        self.minutes_spin = QSpinBox()
        self.minutes_spin.setRange(0, 59)
        self.minutes_spin.setSuffix(" 分钟")
        self.seconds_spin = QSpinBox()
        self.seconds_spin.setRange(1, 59)
        self.seconds_spin.setSuffix(" 秒")
        interval_layout.addWidget(interval_label)
        interval_layout.addWidget(self.days_spin)
        interval_layout.addWidget(self.hours_spin)
        interval_layout.addWidget(self.minutes_spin)
        interval_layout.addWidget(self.seconds_spin)
        layout.addLayout(interval_layout)

        # 对话框按钮
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttonBox.accepted.connect(self.check_and_accept)
        self.buttonBox.rejected.connect(self.reject)
        layout.addWidget(self.buttonBox)

        self.setLayout(layout)
        self.load_config()

    def load_config(self):
        # 填充已有配置，注意执行间隔使用多单位
        self.script_line.setText(self.config.get("script_path", ""))
        self.src_line.setText(self.config.get("src", ""))
        self.tgt_line.setText(self.config.get("tgt", ""))
        self.days_spin.setValue(self.config.get("interval_days", 0))
        self.hours_spin.setValue(self.config.get("interval_hours", 0))
        self.minutes_spin.setValue(self.config.get("interval_minutes", 0))
        self.seconds_spin.setValue(self.config.get("interval_seconds", 10))

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

    def check_and_accept(self):
        # 检查源和目标文件夹是否同时存在且互不包含
        src = self.src_line.text().strip()
        tgt = self.tgt_line.text().strip()
        if src and tgt:
            src_abs = os.path.abspath(src)
            tgt_abs = os.path.abspath(tgt)
            # 如果相等或其中一者是另一者的子目录，视为包含关系
            if src_abs == tgt_abs or src_abs.startswith(tgt_abs + os.sep) or tgt_abs.startswith(src_abs + os.sep):
                QMessageBox.warning(self, "配置错误", "源文件夹与目标文件夹存在包含关系，请选择互不包含的文件夹。")
                return
        self.accept()

    def get_config(self):
        # 返回配置字典，包含多单位的间隔设置
        return {
            "script_path": self.script_line.text().strip(),
            "src": self.src_line.text().strip(),
            "tgt": self.tgt_line.text().strip(),
            "interval_days": self.days_spin.value(),
            "interval_hours": self.hours_spin.value(),
            "interval_minutes": self.minutes_spin.value(),
            "interval_seconds": self.seconds_spin.value()
        }

# ===============================
# 任务项：封装每个脚本任务（增加配置修改信号）
# ===============================
class TaskWidget(QWidget):
    log_signal = pyqtSignal(str)            # 用于向主窗体发送日志信息
    removed_signal = pyqtSignal(object)       # 用于通知删除任务
    config_changed_signal = pyqtSignal()      # 配置变更后发出

    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self.script_module = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.run_task)
        self.running = False
        self.is_executing = False  # 防止并发执行

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

        # 更新脚本按钮
        self.update_btn = QPushButton("更新脚本")
        self.update_btn.clicked.connect(self.update_script)
        layout.addWidget(self.update_btn)

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
            self.script_module = None
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
        # 根据天、小时、分钟、秒计算总间隔（毫秒）
        days = self.config.get("interval_days", 0)
        hours = self.config.get("interval_hours", 0)
        minutes = self.config.get("interval_minutes", 0)
        seconds = self.config.get("interval_seconds", 10)
        total_interval_ms = (days * 86400 + hours * 3600 + minutes * 60 + seconds) * 1000
        self.timer.start(total_interval_ms)
        self.running = True
        self.start_stop_btn.setText("停止")
        self.log(f"任务启动，间隔 {days}天 {hours}时 {minutes}分 {seconds}秒")

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
            self.log("配置已修改")
            self.config_changed_signal.emit()
        else:
            self.log("取消配置修改")

    def update_script(self):
        """
        更新脚本：停止任务、清除旧模块后重新加载，并提示用户重新启动任务。
        """
        if self.running:
            self.stop()

        path = self.config.get("script_path", "")
        module_name = "task_plugin_" + os.path.basename(path).replace(".", "_")
        if module_name in sys.modules:
            del sys.modules[module_name]

        self.load_script_module()
        self.label.setText(os.path.basename(path))
        self.log(f"脚本已重新加载: {os.path.basename(path)}。请重新启动任务以应用更新。")

    def delete_self(self):
        self.stop()
        self.log("任务删除")
        self.removed_signal.emit(self)

    def run_task(self):
        if self.is_executing:
            self.log("上次任务尚未完成，本次执行已跳过")
            return

        self.is_executing = True
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
            self.is_executing = False

    def log(self, message):
        msg = "[{}] {}".format(os.path.basename(self.config.get("script_path", "")), message)
        self.log_signal.emit(msg)

# ===============================
# 主窗口：包含脚本管理和任务日志两个 Tab，同时实现配置记录的加载和保存
# ===============================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("自动化任务平台")
        self.resize(700, 500)
        self.task_widgets = []  # 存储所有任务项

        self.init_ui()
        self.load_tasks_config()

    def init_ui(self):
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # 脚本管理页
        self.manage_tab = QWidget()
        self.manage_layout = QVBoxLayout()
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
            if not config.get("script_path"):
                QMessageBox.warning(self, "配置错误", "请指定脚本文件")
                return
            self.add_task_from_config(config)
            self.append_log("添加任务：" + config.get("script_path"))
            self.save_tasks_config()
        else:
            self.append_log("添加任务已取消")

    def add_task_from_config(self, config):
        task_widget = TaskWidget(config, self)
        task_widget.log_signal.connect(self.append_log)
        task_widget.removed_signal.connect(self.remove_task)
        task_widget.config_changed_signal.connect(self.save_tasks_config)
        self.task_widgets.append(task_widget)
        group = QGroupBox(os.path.basename(config.get("script_path")))
        group_layout = QVBoxLayout()
        group_layout.addWidget(task_widget)
        group.setLayout(group_layout)
        task_widget.group_box = group
        self.task_list_layout.addWidget(group)

    def remove_task(self, task_widget):
        if task_widget in self.task_widgets:
            self.task_widgets.remove(task_widget)
            self.task_list_layout.removeWidget(task_widget.group_box)
            task_widget.group_box.deleteLater()
            self.append_log("删除任务：" + os.path.basename(task_widget.config.get("script_path", "")))
            self.save_tasks_config()

    def append_log(self, message):
        self.log_edit.append(message)

    def load_tasks_config(self):
        if os.path.exists(CONFIG_RECORD_FILE):
            try:
                with open(CONFIG_RECORD_FILE, "r", encoding="utf-8") as f:
                    tasks_config = json.load(f)
                for config in tasks_config:
                    self.add_task_from_config(config)
                self.append_log("加载任务配置成功。")
            except Exception as e:
                self.append_log("加载任务配置失败: " + str(e))

    def save_tasks_config(self):
        tasks_config = [task.config for task in self.task_widgets]
        try:
            with open(CONFIG_RECORD_FILE, "w", encoding="utf-8") as f:
                json.dump(tasks_config, f, ensure_ascii=False, indent=4)
            self.append_log("任务配置已保存。")
        except Exception as e:
            self.append_log("保存任务配置失败: " + str(e))

# ===============================
# 主程序入口
# ===============================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
