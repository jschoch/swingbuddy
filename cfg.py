# This Python file uses the following encoding: utf-8

# if __name__ == "__main__":
#     pass
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox, QCheckBox, QSpinBox
from PySide6.QtCore import Qt,Signal
from swingdb import Config, Swing
# Import Peewee
import peewee as pw
from playhouse.shortcuts import model_to_dict, dict_to_model
db = pw.SqliteDatabase('swingbuddy.db')

class ConfigWindow(QWidget):
    reload_signal = Signal(int)
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Config Editor")
        self.setGeometry(100, 100, 600, 400)
        self.logger = None

        layout = QVBoxLayout()

        # Create input fields and labels
        self.fields = {}
        for field_name in Config._meta.columns.keys():
            row_layout = QHBoxLayout()
            label = QLabel(field_name)
            if field_name == "enableScreen" or field_name == "enableTRC" or field_name == "enablePose" or field_name == "autoplay":
                edit = QCheckBox()
                edit.setChecked(Config._meta.columns[field_name].default)
            elif field_name == "screen_timeout":
                edit = QSpinBox()
                edit.setMinimum(0)
                edit.setValue(Config._meta.columns[field_name].default)
            else:
                edit = QLineEdit()
                edit.setPlaceholderText(Config._meta.columns[field_name].default)

            row_layout.addWidget(label)
            row_layout.addWidget(edit)
            layout.addLayout(row_layout)
            self.fields[field_name] = (label, edit)

        # Add buttons
        button_box = QHBoxLayout()
        load_button = QPushButton("Load Config")
        load_button.clicked.connect(self.load_config)
        save_button = QPushButton("Save Config")
        save_button.clicked.connect(self.save_config)
        button_box.addStretch()
        button_box.addWidget(load_button)
        button_box.addWidget(save_button)
        layout.addLayout(button_box)
        c = self.load_config()
        self.current_config = c
        self.setLayout(layout)

    def load_config(self):
        try:
            config = Config.get_by_id(1)
            for field_name, (label, edit) in self.fields.items():
                value = getattr(config, field_name)
                if isinstance(edit, QCheckBox):
                    edit.setChecked(value)
                elif isinstance(edit, QSpinBox):
                    edit.setValue(value)
                else:
                    edit.setText(str(value))
            return config
        except pw.DoesNotExist:
            QMessageBox.warning(self, "Error", "No configuration found.")

    def save_config(self):
        config = Config.get_or_none()
        if not config:
            config = Config()

        for field_name, (label, edit) in self.fields.items():
                value = getattr(edit, 'isChecked' if isinstance(edit, QCheckBox) else ('value' if isinstance(edit, QSpinBox) else 'text'))

                # Call the method to get the actual value
                value = value() if callable(value) else value

                self.logger.debug(f"Setting {field_name} to {value}")
                setattr(config, field_name, value)


        self.logger.debug(f"config : {model_to_dict(config)}")
        try:
            config.save(force_insert=False)
            self.logger.debug(f"deep deep: {config.id}  type: {type(config.id)}")
            self.reload_signal.emit(config.id)
            QMessageBox.information(self, "Success", "Configuration saved successfully.")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to save configuration: {str(e)}")

    def update_fields_from_model(self, model):
        for field_name, (label, edit) in self.fields.items():
            value = getattr(model, field_name)
            if isinstance(edit, QCheckBox):
                setattr(edit, 'setChecked', value)
            elif isinstance(edit, QSpinBox):
                setattr(edit, 'setValue', value)
            else:
                setattr(edit, 'setText', str(value))
