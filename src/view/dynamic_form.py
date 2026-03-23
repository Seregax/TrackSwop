"""
Dynamic Form for PySide6

Generates Qt widgets based on field specifications.
"""

from typing import List, Optional, Dict, Any, Callable
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QFormLayout,
    QLineEdit,
    QTextEdit,
    QSpinBox,
    QDoubleSpinBox,
    QCheckBox,
    QComboBox,
    QPushButton,
    QLabel,
    QFileDialog,
    QGroupBox,
    QListWidget,
    QListWidgetItem,
)
from PySide6.QtCore import Signal, QObject, Qt
from PySide6.QtGui import QFont

from src.model.specifications.base import Field, FieldType
from src.view.view_model import ViewModel


class DynamicForm(QObject):
    """
    Dynamic form generator for PySide6.
    
    Creates Qt widgets based on field specifications and binds them to ViewModel.
    """
    
    form_validated = Signal(bool)  # Emitted when form is validated (True = valid)
    field_changed = Signal(str)    # Emitted when a field value changes
    
    def __init__(self, fields: List[Field], view_model: ViewModel, parent: Optional[QWidget] = None):
        """
        Initialize the dynamic form.
        
        Args:
            fields: List of field specifications
            view_model: ViewModel to bind fields to
            parent: Parent widget
        """
        super().__init__(parent)
        self.fields = fields
        self.view_model = view_model
        self._widgets: Dict[str, QWidget] = {}
        self._validation_callbacks: Dict[str, List[Callable]] = {}
        
    def create_widget(self, parent: Optional[QWidget] = None) -> QWidget:
        """
        Create the form widget with all fields.
        
        Args:
            parent: Parent widget
            
        Returns:
            QWidget containing the form
        """
        container = QWidget(parent)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Group box for the form
        group = QGroupBox("Настройки")
        form_layout = QFormLayout(group)
        form_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        form_layout.setSpacing(8)
        
        # Create widgets for each field
        for field in self.fields:
            widget = self._create_field_widget(field)
            label = QLabel(field.label)
            
            if field.help_text:
                label.setToolTip(field.help_text)
            
            form_layout.addRow(label, widget)
            self._widgets[field.name] = widget
        
        layout.addWidget(group)
        
        # Validation button
        validate_btn = QPushButton("Применить")
        validate_btn.setMinimumHeight(35)
        validate_btn.setStyleSheet("""
            QPushButton {
                background-color: #1DB954;
                color: white;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1ed760;
            }
        """)
        validate_btn.clicked.connect(self._on_validate_clicked)
        layout.addWidget(validate_btn)
        
        # Error label
        self._error_label = QLabel("")
        self._error_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
        self._error_label.setWordWrap(True)
        layout.addWidget(self._error_label)
        
        return container
    
    def _create_field_widget(self, field: Field) -> QWidget:
        """
        Create a widget for a specific field.
        
        Args:
            field: Field specification
            
        Returns:
            QWidget for the field
        """
        widget: QWidget = None
        
        if field.field_type == FieldType.STRING:
            widget = QLineEdit()
            widget.setPlaceholderText(field.placeholder or "")
            if field.default:
                widget.setText(str(field.default))
            widget.textChanged.connect(lambda v: self._on_field_changed(field.name, v))
            
        elif field.field_type == FieldType.TEXT:
            widget = QTextEdit()
            widget.setPlaceholderText(field.placeholder or "")
            widget.setMaximumHeight(100)
            if field.default:
                widget.setPlainText(str(field.default))
            widget.textChanged.connect(lambda: self._on_field_changed(field.name, widget.toPlainText()))
            
        elif field.field_type == FieldType.PASSWORD:
            widget = QLineEdit()
            widget.setPlaceholderText(field.placeholder or "")
            widget.setEchoMode(QLineEdit.EchoMode.Password)
            if field.default:
                widget.setText(str(field.default))
            widget.textChanged.connect(lambda v: self._on_field_changed(field.name, v))
            
        elif field.field_type == FieldType.NUMBER:
            widget = QDoubleSpinBox()
            widget.setRange(-1e9, 1e9)
            widget.setDecimals(0)
            if field.default is not None:
                widget.setValue(float(field.default))
            if field.placeholder:
                widget.lineEdit().setPlaceholderText(field.placeholder)
            widget.valueChanged.connect(lambda v: self._on_field_changed(field.name, v))
            
        elif field.field_type == FieldType.BOOLEAN:
            widget = QCheckBox()
            if field.default:
                widget.setChecked(True)
            widget.stateChanged.connect(lambda v: self._on_field_changed(field.name, v == Qt.CheckState.Checked))
            
        elif field.field_type == FieldType.FOLDER:
            widget = self._create_file_picker_widget(field, mode="directory")
            
        elif field.field_type == FieldType.FILE:
            widget = self._create_file_picker_widget(field, mode="file")
            
        elif field.field_type == FieldType.CHOICE:
            widget = QComboBox()
            for idx, choice in enumerate(field.choices):
                widget.addItem(choice["label"], choice["value"])
                if field.default and choice["value"] == field.default:
                    widget.setCurrentIndex(idx)
            widget.currentIndexChanged.connect(
                lambda: self._on_field_changed(field.name, widget.currentData())
            )
            
        elif field.field_type == FieldType.MULTI_CHOICE:
            widget = QListWidget()
            widget.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
            widget.setMaximumHeight(150)
            for idx, choice in enumerate(field.choices):
                item = QListWidgetItem(choice["label"])
                item.setData(Qt.ItemDataRole.UserRole, choice["value"])
                widget.addItem(item)
            widget.itemSelectionChanged.connect(
                lambda: self._on_field_changed(field.name, self._get_multi_choice_values(widget))
            )
        
        if widget is None:
            widget = QLineEdit()
            widget.setPlaceholderText("Unsupported field type")
        
        # Set tooltip if help text exists
        if field.help_text:
            widget.setToolTip(field.help_text)
        
        return widget
    
    def _create_file_picker_widget(self, field: Field, mode: str = "file") -> QWidget:
        """
        Create a file/folder picker widget.

        Args:
            field: Field specification
            mode: "file" or "directory"

        Returns:
            QWidget with line edit and browse button
        """
        from PySide6.QtWidgets import QHBoxLayout
        
        container = QWidget()
        h_layout = QHBoxLayout(container)
        h_layout.setContentsMargins(0, 0, 0, 0)
        h_layout.setSpacing(4)

        # Line edit
        line_edit = QLineEdit()
        line_edit.setPlaceholderText(field.placeholder or "Выберите путь...")
        if field.default:
            line_edit.setText(str(field.default))
        h_layout.addWidget(line_edit, stretch=1)

        # Browse button
        browse_btn = QPushButton("...")
        browse_btn.setMaximumWidth(40)
        browse_btn.clicked.connect(lambda: self._on_browse_clicked(line_edit, mode))
        h_layout.addWidget(browse_btn)

        # Bind to view model
        line_edit.textChanged.connect(lambda v: self._on_field_changed(field.name, v))

        return container
    
    def _on_browse_clicked(self, line_edit: QLineEdit, mode: str):
        """
        Handle browse button click.
        
        Args:
            line_edit: Line edit to update with selected path
            mode: "file" or "directory"
        """
        if mode == "directory":
            path = QFileDialog.getExistingDirectory(
                self.parent(),
                "Выберите директорию",
                line_edit.text() or "",
            )
        else:
            path, _ = QFileDialog.getOpenFileName(
                self.parent(),
                "Выберите файл",
                line_edit.text() or "",
            )
        
        if path:
            line_edit.setText(path)
    
    def _get_multi_choice_values(self, list_widget: QListWidget) -> List[Any]:
        """
        Get selected values from multi-choice list.
        
        Args:
            list_widget: QListWidget with selections
            
        Returns:
            List of selected values
        """
        values = []
        for i in range(list_widget.count()):
            item = list_widget.item(i)
            if item.isSelected():
                values.append(item.data(Qt.ItemDataRole.UserRole))
        return values
    
    def _on_field_changed(self, field_name: str, value: Any):
        """
        Handle field value change.
        
        Args:
            field_name: Field name
            value: New value
        """
        self.view_model.set_value(field_name, value)
        self.field_changed.emit(field_name)
    
    def _on_validate_clicked(self):
        """
        Validate all fields and update ViewModel.
        """
        errors = []
        
        for field in self.fields:
            value = self.view_model.get_value(field.name)
            field_errors = field.validate(value)
            
            if field_errors:
                errors.extend([f"{field.label}: {e}" for e in field_errors])
        
        if errors:
            self._error_label.setText("\n".join(errors))
            self.form_validated.emit(False)
        else:
            self._error_label.setText("")
            self.form_validated.emit(True)
    
    def get_values(self) -> Dict[str, Any]:
        """
        Get all field values from ViewModel.
        
        Returns:
            Dictionary of field name -> value
        """
        return {field.name: self.view_model.get_value(field.name) for field in self.fields}
    
    def set_values(self, values: Dict[str, Any]):
        """
        Set field values from dictionary.
        
        Args:
            values: Dictionary of field name -> value
        """
        for field_name, value in values.items():
            self.view_model.set_value(field_name, value)
            
            # Update widget if exists
            widget = self._widgets.get(field_name)
            if widget:
                self._update_widget_from_value(widget, value)
    
    def _update_widget_from_value(self, widget: QWidget, value: Any):
        """
        Update widget display from value.
        
        Args:
            widget: Widget to update
            value: Value to display
        """
        if isinstance(widget, QLineEdit):
            widget.setText(str(value) if value is not None else "")
        elif isinstance(widget, QTextEdit):
            widget.setPlainText(str(value) if value is not None else "")
        elif isinstance(widget, QCheckBox):
            widget.setChecked(bool(value))
        elif isinstance(widget, QSpinBox) or isinstance(widget, QDoubleSpinBox):
            widget.setValue(float(value) if value is not None else 0)
        elif isinstance(widget, QComboBox):
            idx = widget.findData(value)
            if idx >= 0:
                widget.setCurrentIndex(idx)
