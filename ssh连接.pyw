import sys
import os
import paramiko
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QComboBox, QPushButton,
                             QLabel, QSplitter, QFileDialog, QMessageBox, QTextEdit, QListWidget)
from terminal import Terminal
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QColor
from version_checker import VersionChecker, show_update_dialog

class SSHThread(QThread):
    output_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    def __init__(self, host, port, username, password):
        super().__init__()
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.ssh = None
        self.channel = None

    def run(self):
        try:
            self.ssh = paramiko.SSHClient()
            self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.ssh.connect(self.host, self.port, self.username, self.password)
            self.channel = self.ssh.invoke_shell()
            while True:
                if self.channel.recv_ready():
                    data = self.channel.recv(1024)
                    self.output_signal.emit(data.decode('utf-8'))
        except Exception as e:
            self.error_signal.emit(str(e))
 
    def send_command(self, command):
        if self.channel:
            self.channel.send(command + '\n')

class SSHClient(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ssh_thread = None
        self.commands = {}
        
        # 设置窗口图标
        icon_path = os.path.join(os.path.dirname(__file__), 'ssh.ico')
        if os.path.exists(icon_path):
            from PyQt5.QtGui import QIcon
            self.setWindowIcon(QIcon(icon_path))

        # 初始化版本检查器
        self.version_checker = VersionChecker('1.1.2', 'https://s.lekuidc.com/version.json')
        self.version_checker.update_available.connect(self.on_update_available)

        self.init_ui()
        self.load_config()
        self.load_commands()
        
        # 检查更新
        self.version_checker.check_for_updates()

    def on_update_available(self, version, download_url):
        show_update_dialog(self, version, download_url)

    def init_ui(self):
        self.setWindowTitle('小白SSH工具 1.2.0  开发者@Ammkiss')
        # 设置窗口居中
        screen = QApplication.primaryScreen().geometry()
        window_width = 1200
        window_height = 600  # 将窗口高度从800减少到600
        x = (screen.width() - window_width) // 2
        y = 200
        self.setGeometry(x, y, window_width, window_height)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 5, 0, 5)  # 减小上下边距
        layout.setSpacing(3)  # 将整体垂直间距改为3px

        # 菜单栏调整
        menu_bar = QWidget()
        menu_layout = QHBoxLayout(menu_bar)
        menu_layout.setContentsMargins(10, 0, 10, 0)
        menu_layout.setSpacing(0)  # 减小菜单项之间的间距

        # 创建5个链接标签
        menu_names = ['软件官网 ', '服务器租用', 'TG频道', 'GitHub仓库', '常见问题']
        menu_links = ['', '', '', '', '']
        for i, (name, link) in enumerate(zip(menu_names, menu_links)):
            link_label = QLabel(name)
            if i == 0:  # 第一个菜单项（项目介绍）
                link_label.setStyleSheet("""
                    QLabel {
                        color: #333333;
                        padding: 6px 0px 6px 0px;  /* 第一个菜单项左padding为0 */
                        border-radius: 4px;
                        font-size: 12px;
                        margin: 0;
                    }
                    QLabel:hover {
                        background-color: #f0f0f0;
                        color: #1a73e8;
                        padding: 6px 8px;  /* hover时添加padding */
                    }
                """)
            else:
                link_label.setStyleSheet("""
                    QLabel {
                        color: #333333;
                        padding: 6px 8px;  /* 其他菜单项保持左右padding一致 */
                        border-radius: 4px;
                        font-size: 12px;
                        margin: 0;
                    }
                    QLabel:hover {
                        background-color: #f0f0f0;
                        color: #1a73e8;
                    }
                """)
            def create_click_handler(url):
                def click_handler(event):
                    import webbrowser
                    webbrowser.open(url)
                    event.accept()
                return click_handler
            link_label.mousePressEvent = create_click_handler(link)
            menu_layout.addWidget(link_label)

        menu_layout.addStretch()
        layout.addWidget(menu_bar)

        # 顶部控制栏调整
        top_bar = QWidget()
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(10, 3, 10, 3)  # 减小上下边距

        # 服务器选择区域样式
        self.server_combo = QComboBox()
        self.server_combo.setMinimumWidth(300)
        self.server_combo.setStyleSheet("""
            QComboBox {
                padding: 8px 15px;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                background-color: white;
                font-size: 13px;
                color: #333333;
            }
            QComboBox:hover {
                border-color: #1a73e8;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
                padding-right: 8px;
            }
            QComboBox::down-arrow {
                width: 0;
                height: 0;
                border-left: 8px solid transparent;
                border-right: 8px solid transparent;
                border-top: 8px solid #333333;
                margin-right: 8px;
            }
            QComboBox QAbstractItemView {
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                background-color: white;
                selection-background-color: #f5f5f5;
                selection-color: #333333;
                padding: 4px;
            }
            QComboBox QAbstractItemView::item {
                height: 32px;  /* 调整每项的高度 */
                padding: 0 15px;  /* 左右padding */
                border-radius: 4px;
                color: #333333;
                font-size: 13px;
                min-height: 32px;  /* 确保最小高度 */
                margin: 1px 4px;  /* 项目之间的间距 */
            }
            QComboBox QAbstractItemView::item:hover {
                background-color: #f8f9fa;
            }
            QComboBox QAbstractItemView::item:selected {
                background-color: #f0f0f0;
            }
        """)
        top_layout.addWidget(self.server_combo)

        # 按钮样式
        button_style = """
            QPushButton {
                padding: 8px 25px;
                border-radius: 4px;
                font-size: 13px;
                font-weight: normal;
                border: none;
                color: #333333;
                background-color: #e8eaed;
                margin: 0 2px;
            }
            QPushButton:hover {
                background-color: #dadce0;
                color: #1a73e8;
            }
            QPushButton:pressed {
                background-color: #cacccf;
                color: #1557b0;
            }
            QPushButton:disabled {
                background-color: #e8eaed;
                color: #9aa0a6;
            }
        """

        self.connect_btn = QPushButton('连接')
        self.connect_btn.setStyleSheet(button_style)
        self.connect_btn.clicked.connect(self.connect_ssh)
        top_layout.addWidget(self.connect_btn)

        self.upload_btn = QPushButton('上传')
        self.upload_btn.setStyleSheet(button_style)
        self.upload_btn.clicked.connect(self.upload_file)
        top_layout.addWidget(self.upload_btn)

        self.download_btn = QPushButton('下载')
        self.download_btn.setStyleSheet(button_style)
        self.download_btn.clicked.connect(self.download_ip_file)
        top_layout.addWidget(self.download_btn)

        top_layout.addStretch()
        layout.addWidget(top_bar)

        # 终端输出区域
        self.terminal = Terminal()
        self.terminal.setFont(QFont('Consolas', 11))
        self.terminal.setStyleSheet("""
            QWidget {
                background-color: #282c34;
                color: #abb2bf;
                border: 1px solid #3e4451;
                border-radius: 6px;
                padding: 5px;
                margin: 0 10px;
            }
        """)
        self.terminal.setMinimumHeight(350)  # 减小终端区域高度
        layout.addWidget(self.terminal, 2)

        # 命令输入区域调整
        input_area = QWidget()
        input_layout = QHBoxLayout(input_area)
        input_layout.setContentsMargins(10, 3, 10, 3)  # 减小上下边距
        input_layout.setSpacing(10)
        
        self.command_input = QTextEdit()
        self.command_input.setFixedHeight(45)  # 保持输入框高度
        self.command_input.setFont(QFont('Consolas', 11))
        self.command_input.setStyleSheet("""
            QTextEdit {
                border: 1px solid #dcdcdc;
                border-radius: 4px;
                padding: 8px 12px;
                background-color: white;
            }
            QTextEdit:focus {
                border-color: #1a73e8;
            }
        """)
        self.command_input.installEventFilter(self)
        input_layout.addWidget(self.command_input, 1)  # 设置拉伸因子为1，使输入框占据更多空间

        # 发送按钮
        self.send_btn = QPushButton('发送')
        self.send_btn.setFixedSize(80, 45)  # 调整按钮宽度
        self.send_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 15px;
                border-radius: 4px;
                font-size: 13px;
                font-weight: 500;
                border: none;
                color: white;
                background-color: #2ecc71;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
            QPushButton:pressed {
                background-color: #219a52;
            }
        """)
        self.send_btn.clicked.connect(self.send_command)
        input_layout.addWidget(self.send_btn)

        layout.addWidget(input_area, 0)

        # 命令分类和列表区域调整
        command_area = QWidget()
        command_layout = QHBoxLayout(command_area)
        command_layout.setContentsMargins(10, 3, 10, 3)
        command_layout.setSpacing(10)

        list_style = """
            QListWidget {
                border: 1px solid #dcdcdc;
                border-radius: 4px;
                background-color: white;
                padding: 8px;
            }
            QListWidget::item {
                padding: 10px;
                border-radius: 4px;
                margin: 2px 0;
            }
            QListWidget::item:hover {
                background-color: #f5f5f5;
            }
            QListWidget::item:selected {
                background-color: #e8f0fe;
                color: #1a73e8;
            }
        """

        self.category_list = QListWidget()
        self.category_list.setFont(QFont('Microsoft YaHei', 11))
        self.category_list.setMaximumWidth(220)
        self.category_list.setMinimumWidth(220)
        self.category_list.setMinimumHeight(260)  # 从200px增加到260px
        self.category_list.setStyleSheet(list_style)
        self.category_list.currentRowChanged.connect(self.on_category_changed)
        command_layout.addWidget(self.category_list)

        self.command_list = QListWidget()
        self.command_list.setFont(QFont('Microsoft YaHei', 11))
        self.command_list.setMinimumHeight(260)  # 从200px增加到260px
        self.command_list.setStyleSheet(list_style)
        self.command_list.itemDoubleClicked.connect(self.on_command_selected)
        command_layout.addWidget(self.command_list)

        layout.addWidget(command_area, 0)  # 保持拉伸因子为0

        # 调整菜单栏和服务器区域之间的间距
        layout.setSpacing(3)  # 设置整体布局的垂直间距为3px

    def eventFilter(self, obj, event):
        if obj == self.command_input and event.type() == event.KeyPress:
            if event.modifiers() == Qt.ShiftModifier and event.key() == Qt.Key_Return:
                self.send_command()
                return True
        return super().eventFilter(obj, event)

    def load_commands(self):
        try:
            script_path = 'jiaoben.txt'
            if not os.path.exists(script_path):
                script_path = os.path.join(os.path.dirname(__file__), 'jiaoben.txt')
            
            with open(script_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                current_category = None
                current_commands = []
                
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                        
                    if line.startswith('====') and line.endswith('===='):
                        if current_category and current_commands:
                            self.commands[current_category] = current_commands
                            self.category_list.addItem(current_category)
                        current_category = line
                        current_commands = []
                    elif '=' in line and current_category:
                        name, cmd = line.split('=', 1)
                        current_commands.append((name, cmd))
                
                # 添加最后一个分类的命令
                if current_category and current_commands:
                    self.commands[current_category] = current_commands
                    self.category_list.addItem(current_category)
                    
                # 自动选择第一个分类
                if self.category_list.count() > 0:
                    self.category_list.setCurrentRow(0)
                    
        except Exception as e:
            QMessageBox.warning(self, '错误', f'加载命令配置文件失败: {str(e)}')
            # 如果加载失败，使用硬编码的默认配置
            self._load_default_commands()
    
    def _load_default_commands(self):
        commands_config = {
            '====常用命定====': [
                ('系统信息', 'hostname -I'),
                ('查看内存使用', 'free -h'),
                ('查看磁盘使用', 'df -h'),
                ('查看系统负载', 'top')
            ],
            '====宝塔====': [
                ('宝塔官方版', 'yum install -y wget && wget -O install.sh https://download.bt.cn/install/install_6.0.sh && sh install.sh ed8484bec'),
                ('宝塔开心版', 'curl https://io.bt.sy/install/update_panel.sh|bash')
            ],
            '====CentOS====': [
                ('查看系统版本', 'cat /etc/redhat-release')
            ],
            '====Ubuntu ====': [
                ('查看系统版本', 'lsb_release -a'),
                ('更新软件包列表', 'apt update'),
                ('升级软件包', 'apt upgrade'),
                ('安装软件', 'apt install'),
                ('卸载软件', 'apt remove')
            ]
        }
        
        for category, commands in commands_config.items():
            self.commands[category] = commands
            self.category_list.addItem(category)

    def on_category_changed(self, row):
        self.command_list.clear()
        if row >= 0:
            category = self.category_list.item(row).text()
            if category in self.commands:
                for name, _ in self.commands[category]:
                    self.command_list.addItem(name)

    def send_command(self):
        if not self.ssh_thread:
            QMessageBox.warning(self, '警告', '请先连接到服务器')
            return
        command = self.command_input.toPlainText().strip()
        if command:
            self.ssh_thread.send_command(command)
            self.command_input.clear()

    def on_command_selected(self, item):
        if not self.ssh_thread:
            QMessageBox.warning(self, '警告', '请先连接到服务器')
            return

        command_name = item.text()
        for category in self.commands:
            for name, cmd in self.commands[category]:
                if name == command_name:
                    # 直接发送命令到SSH通道，不显示命令本身
                    if self.ssh_thread.channel:
                        # 在命令前后添加特殊字符，用于在输出中隐藏命令
                        self.ssh_thread.channel.send('clear && ' + cmd + ' 2>&1\n')
                    break

    def connect_ssh(self):
        if self.connect_btn.text() == '连接':
            server_data = self.server_combo.currentData()
            if not server_data:
                QMessageBox.warning(self, '警告', '请选择要连接的服务器')
                return

            self.ssh_thread = SSHThread(
                server_data['host'],
                server_data['port'],
                server_data['username'],
                server_data['password']
            )
            self.ssh_thread.output_signal.connect(self.terminal.append)
            self.ssh_thread.error_signal.connect(lambda msg: QMessageBox.critical(self, '错误', msg))
            self.ssh_thread.start()
            self.connect_btn.setText('断开')
            self.server_combo.setEnabled(False)  # 禁用服务器选择下拉框
        else:
            if self.ssh_thread:
                self.ssh_thread.terminate()
                self.ssh_thread = None
            self.connect_btn.setText('连接')
            self.server_combo.setEnabled(True)  # 重新启用服务器选择下拉框

    def download_ip_file(self):
        if not self.ssh_thread or not self.ssh_thread.ssh:
            QMessageBox.warning(self, '警告', '请先连接到服务器')
            return

        try:
            sftp = self.ssh_thread.ssh.open_sftp()
            try:
                # 获取/root/ip目录下的所有txt文件
                try:
                    files = sftp.listdir('/root/ip')
                    txt_files = [f for f in files if f.endswith('.txt')]
                    
                    if not txt_files:
                        QMessageBox.warning(self, '提示', '/root/ip目录下没有找到txt文件')
                        return
                        
                    # 如果只有一个txt文件，直接下载
                    if len(txt_files) == 1:
                        file_name = txt_files[0]
                        file_path, _ = QFileDialog.getSaveFileName(self, '保存文件', file_name, 'Text Files (*.txt)')
                        if file_path:
                            sftp.get(f'/root/ip/{file_name}', file_path)
                            QMessageBox.information(self, '成功', f'文件 {file_name} 下载成功！')
                    else:
                        # 如果有多个txt文件，创建一个临时目录来保存
                        save_dir = QFileDialog.getExistingDirectory(self, '选择保存目录')
                        if save_dir:
                            success_count = 0
                            for file_name in txt_files:
                                try:
                                    local_path = os.path.join(save_dir, file_name)
                                    sftp.get(f'/root/ip/{file_name}', local_path)
                                    success_count += 1
                                except Exception as e:
                                    print(f'下载文件 {file_name} 时出错: {str(e)}')
                            
                            if success_count > 0:
                                QMessageBox.information(self, '成功', f'成功下载了 {success_count} 个文件到 {save_dir}')
                            else:
                                QMessageBox.warning(self, '错误', '没有文件被成功下载')
                                
                except Exception as e:
                    QMessageBox.warning(self, '错误', f'无法访问 /root/ip 目录：{str(e)}')
                    return

            finally:
                sftp.close()
        except Exception as e:
            QMessageBox.critical(self, '错误', f'下载时发生错误：{str(e)}')

    def upload_file(self):
        if not self.ssh_thread or not self.ssh_thread.ssh:
            QMessageBox.warning(self, '警告', '请先连接到服务器')
            return

        try:
            file_path, _ = QFileDialog.getOpenFileName(self, '选择要上传的文件')
            if file_path:
                sftp = self.ssh_thread.ssh.open_sftp()
                try:
                    remote_path = f'/root/{os.path.basename(file_path)}'
                    sftp.put(file_path, remote_path)
                    QMessageBox.information(self, '成功', f'文件已成功上传到 {remote_path}')
                finally:
                    sftp.close()
        except Exception as e:
            QMessageBox.critical(self, '错误', f'上传文件时发生错误：{str(e)}')

    def open_link(self, index):
        import webbrowser
        webbrowser.open(f'http://s{index}.leku.co/')

    def load_config(self):
        try:
            config_path = 'comfig.txt'
            if not os.path.exists(config_path):
                config_path = os.path.join(os.path.dirname(__file__), 'comfig.txt')
                if not os.path.exists(config_path):
                    QMessageBox.warning(self, '错误', '配置文件不存在，请确保comfig.txt文件在程序目录下')
                    return

            # 尝试使用不同的编码方式读取文件
            encodings = ['utf-8-sig', 'utf-8', 'gbk', 'gb2312', 'ansi']
            content = None
            encoding_used = None
            for encoding in encodings:
                try:
                    with open(config_path, 'r', encoding=encoding) as f:
                        content = f.read()
                        encoding_used = encoding
                        break
                except UnicodeDecodeError:
                    continue

            if content is None:
                QMessageBox.warning(self, '错误', '无法读取配置文件，请确保文件编码格式正确')
                return

            lines = content.splitlines()
            current_server = {}
            server_count = 0

            for line in lines:
                line = line.strip()
                if line:
                    if line.startswith('服务器名称:'):
                        if current_server:
                            if all(key in current_server for key in ['name', 'host', 'username', 'port', 'password']):
                                self.server_combo.addItem(current_server['name'], current_server)
                                server_count += 1
                            else:
                                QMessageBox.warning(self, '错误', f'服务器 {current_server.get("name", "未知")} 配置不完整\n请确保包含：服务器名称、IP、用户名、端口、密码')
                        current_server = {'name': line.split(':', 1)[1].strip()}
                    elif ':' in line:
                        key, value = line.split(':', 1)
                        value = value.strip()
                        if key == 'IP':
                            current_server['host'] = value
                        elif key == '用户名':
                            current_server['username'] = value
                        elif key == '端口':
                            try:
                                current_server['port'] = int(value)
                            except ValueError:
                                QMessageBox.warning(self, '错误', f'服务器 {current_server.get("name", "未知")} 的端口号格式错误')
                        elif key == '密码':
                            current_server['password'] = value

            # 处理最后一个服务器配置
            if current_server:
                if all(key in current_server for key in ['name', 'host', 'username', 'port', 'password']):
                    self.server_combo.addItem(current_server['name'], current_server)
                    server_count += 1
                else:
                    QMessageBox.warning(self, '错误', f'服务器 {current_server.get("name", "未知")} 配置不完整\n请确保包含：服务器名称、IP、用户名、端口、密码')

            if server_count == 0:
                QMessageBox.warning(self, '错误', '未找到有效的服务器配置，请检查配置文件格式是否正确')

        except Exception as e:
            QMessageBox.warning(self, '错误', f'加载配置文件失败: {str(e)}\n请确保配置文件格式正确且不包含特殊字符')

if __name__ == '__main__':
    app = QApplication(sys.argv)
    client = SSHClient()
    client.show()
    sys.exit(app.exec_())
