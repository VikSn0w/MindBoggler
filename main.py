from __future__ import annotations
from dataclasses import dataclass, field
from typing import Set
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction, QKeySequence, QTextCharFormat, QColor, QTextOption, QTextCursor, QIcon
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QSplitter, QVBoxLayout, QHBoxLayout,
    QPlainTextEdit, QPushButton, QLabel, QTableWidget, QTableWidgetItem,
    QFileDialog, QMessageBox, QToolBar, QStatusBar, QAbstractItemView, QTextEdit,
    QInputDialog, QDialog, QButtonGroup, QRadioButton, QGroupBox, QCheckBox
)
from interpreter import Interpreter, PointerBehavior, PointerOverflowError


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setModal(True)
        self.resize(400, 300)
        layout = QVBoxLayout(self)

        # Pointer behavior group
        pointer_group = QGroupBox("Pointer Behavior")
        pointer_layout = QVBoxLayout(pointer_group)

        self.pointer_behavior_group = QButtonGroup(self)

        self.clamp_radio = QRadioButton("Clamp (safe - stays at boundaries)")
        self.wrap_radio = QRadioButton("Wrap-around (circular memory)")
        self.error_radio = QRadioButton("Error on overflow/underflow")

        self.pointer_behavior_group.addButton(self.clamp_radio, PointerBehavior.CLAMP.value)
        self.pointer_behavior_group.addButton(self.wrap_radio, PointerBehavior.WRAP.value)
        self.pointer_behavior_group.addButton(self.error_radio, PointerBehavior.ERROR.value)

        # Set default
        self.clamp_radio.setChecked(True)

        pointer_layout.addWidget(self.clamp_radio)
        pointer_layout.addWidget(self.wrap_radio)
        pointer_layout.addWidget(self.error_radio)

        # Add descriptions
        desc_label = QLabel(
            "• Clamp: Pointer stops at memory boundaries (0 and memory_size-1)\n"
            "• Wrap-around: Pointer wraps to opposite end when crossing boundaries\n"
            "• Error: Throw exception when pointer goes out of bounds"
        )
        desc_label.setStyleSheet("color: gray; font-size: 9pt;")
        pointer_layout.addWidget(desc_label)

        layout.addWidget(pointer_group)

        # Cell overflow behavior group
        cell_group = QGroupBox("Cell Value Behavior")
        cell_layout = QVBoxLayout(cell_group)

        self.cell_wrap_checkbox = QCheckBox("Wrap cell values (0-255, standard Brainfuck)")
        self.cell_wrap_checkbox.setChecked(True)
        cell_layout.addWidget(self.cell_wrap_checkbox)

        cell_desc = QLabel("When unchecked, cell values can exceed 0-255 range")
        cell_desc.setStyleSheet("color: gray; font-size: 9pt;")
        cell_layout.addWidget(cell_desc)

        layout.addWidget(cell_group)

        # Buttons
        button_layout = QHBoxLayout()
        self.ok_button = QPushButton("OK")
        self.cancel_button = QPushButton("Cancel")

        button_layout.addStretch()
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)

        layout.addLayout(button_layout)

        # Connect buttons
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

    def get_pointer_behavior(self):
        return PointerBehavior(self.pointer_behavior_group.checkedId())

    def set_pointer_behavior(self, behavior: PointerBehavior):
        if behavior == PointerBehavior.CLAMP:
            self.clamp_radio.setChecked(True)
        elif behavior == PointerBehavior.WRAP:
            self.wrap_radio.setChecked(True)
        elif behavior == PointerBehavior.ERROR:
            self.error_radio.setChecked(True)

    def get_cell_wrap(self):
        return self.cell_wrap_checkbox.isChecked()

    def set_cell_wrap(self, wrap: bool):
        self.cell_wrap_checkbox.setChecked(wrap)


class CompileOutputDialog(QDialog):
    def __init__(self, parent=None, title="Compilation Results", content=""):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(800, 600)

        layout = QVBoxLayout(self)

        self.text_area = QPlainTextEdit()
        self.text_area.setPlainText(content)
        self.text_area.setReadOnly(True)
        self.text_area.setFont(self.font())

        layout.addWidget(self.text_area)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)


@dataclass
class FormatColors:
    current: QColor = field(default_factory=lambda: QColor(255, 255, 0, 90))
    breakpoint: QColor = field(default_factory=lambda: QColor(255, 0, 0, 90))


class CodeEditor(QPlainTextEdit):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWordWrapMode(QTextOption.NoWrap)
        self.breakpoint_indices: Set[int] = set()
        self.colors = FormatColors()
        self.shortcut_breakpoint = QAction(self)
        self.shortcut_breakpoint.setShortcut(QKeySequence("F9"))
        self.shortcut_breakpoint.triggered.connect(self.toggle_breakpoint_at_caret)
        self.addAction(self.shortcut_breakpoint)

    def toggle_breakpoint_at_caret(self):
        idx = self.textCursor().position()
        idx = max(0, min(idx, len(self.toPlainText()) - 1))
        if idx in self.breakpoint_indices:
            self.breakpoint_indices.remove(idx)
        else:
            self.breakpoint_indices.add(idx)
        self.update_highlighting(current_pc=None)

    def update_highlighting(self, current_pc: int | None):
        extra = []
        doc = self.document()

        def make_sel(start: int, length: int, color: QColor):
            sel = QTextEdit.ExtraSelection()
            fmt = QTextCharFormat()
            fmt.setBackground(color)
            sel.format = fmt
            cur = self.textCursor()
            cur.setPosition(max(0, min(start, doc.characterCount() - 1)))
            cur.setPosition(max(0, min(start + max(1, length), doc.characterCount() - 1)), QTextCursor.KeepAnchor)
            sel.cursor = cur
            return sel

        if current_pc is not None and 0 <= current_pc < doc.characterCount():
            extra.append(make_sel(current_pc, 1, self.colors.current))
        for i in self.breakpoint_indices:
            if 0 <= i < doc.characterCount():
                extra.append(make_sel(i, 1, self.colors.breakpoint))
        self.setExtraSelections(extra)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mind Boggler - Brainfuck PyIDE")
        self.resize(1200, 800)
        self.setWindowIcon(QIcon("icon.png"))
        self.interp = Interpreter()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._on_timer)

        # Settings
        self.settings = {
            'pointer_behavior': PointerBehavior.CLAMP,
            'cell_wrap': True
        }

        # Configure interpreter with initial settings
        self.interp.configure(self.settings['pointer_behavior'], self.settings['cell_wrap'])

        if hasattr(self.interp, 'setInputCallback'):
            self.interp.setInputCallback(self._request_input)

        self.execution_mode = 2
        self.paused_at_breakpoint = False

        self.timer_intervals = {
            0: 100,
            1: 500,
            2: 1
        }

        self._build_ui()
        self._connect_actions()
        self._load_sample()

    def _build_ui(self):
        self.editor = CodeEditor()
        self.output = QPlainTextEdit(readOnly=True)
        self.output.setPlaceholderText("Program output will appear here…")

        self.mem_table = QTableWidget(32, 16)
        self.mem_table.setHorizontalHeaderLabels([f"{i:X}" for i in range(16)])
        self.mem_table.setVerticalHeaderLabels([f"{i:04X}" for i in range(32)])
        self.mem_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.mem_table.setSelectionMode(QAbstractItemView.NoSelection)
        self.mem_table.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.mem_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.btn_run = QPushButton("Run")
        self.btn_step = QPushButton("Step")
        self.btn_pause = QPushButton("Pause")
        self.btn_resume = QPushButton("Resume")
        self.btn_reset = QPushButton("Reset")
        self.btn_clear_out = QPushButton("Clear Output")

        self.btn_resume.hide()

        mode_group = QButtonGroup(self)
        self.mode_debug = QRadioButton("Debug")
        self.mode_slow = QRadioButton("Slow (2/sec)")
        self.mode_fast = QRadioButton("Fast")
        self.mode_fast.setChecked(True)

        mode_group.addButton(self.mode_debug, 0)
        mode_group.addButton(self.mode_slow, 1)
        mode_group.addButton(self.mode_fast, 2)
        mode_group.buttonClicked.connect(self._on_mode_changed)

        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("Mode:"))
        mode_layout.addWidget(self.mode_debug)
        mode_layout.addWidget(self.mode_slow)
        mode_layout.addWidget(self.mode_fast)
        mode_layout.addStretch()

        controls = QHBoxLayout()
        for w in (self.btn_run, self.btn_step, self.btn_pause, self.btn_resume,
                  self.btn_reset, self.btn_clear_out):
            controls.addWidget(w)
        controls.addStretch(1)

        left = QWidget()
        lyt_left = QVBoxLayout(left)
        lyt_left.addWidget(QLabel("Code"))
        lyt_left.addWidget(self.editor)
        lyt_left.addLayout(mode_layout)
        lyt_left.addLayout(controls)

        right = QWidget()
        lyt_right = QVBoxLayout(right)
        lyt_right.addWidget(QLabel("Output"))
        lyt_right.addWidget(self.output)
        lyt_right.addWidget(QLabel("Memory (hex grid around pointer)"))
        lyt_right.addWidget(self.mem_table)

        splitter = QSplitter()
        splitter.addWidget(left)
        splitter.addWidget(right)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)
        self.setCentralWidget(splitter)

        tb = QToolBar("Main")
        self.addToolBar(tb)
        self.act_open = QAction("Open…", self)
        self.act_save = QAction("Save As…", self)
        self.act_check = QAction("Check Syntax", self)
        self.act_break = QAction("Toggle Breakpoint (F9)", self)
        self.act_break.setShortcut(QKeySequence("F9"))
        self.act_compile = QAction("Compile & Show", self)
        self.act_pseudocode = QAction("Generate Pseudocode", self)
        self.act_settings = QAction("Settings…", self)
        tb.addAction(self.act_open)
        tb.addAction(self.act_save)
        tb.addSeparator()
        tb.addAction(self.act_check)
        tb.addAction(self.act_compile)
        tb.addAction(self.act_pseudocode)
        tb.addAction(self.act_break)
        tb.addSeparator()
        tb.addAction(self.act_settings)

        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self._update_status()
        self._refresh_memory()

    def _connect_actions(self):
        self.btn_run.clicked.connect(self.on_run)
        self.btn_step.clicked.connect(self.on_step)
        self.btn_pause.clicked.connect(self.on_pause)
        self.btn_resume.clicked.connect(self.on_resume)
        self.btn_reset.clicked.connect(self.on_reset)
        self.btn_clear_out.clicked.connect(lambda: self.output.setPlainText(""))
        self.act_open.triggered.connect(self.on_open)
        self.act_save.triggered.connect(self.on_save)
        self.act_check.triggered.connect(self.on_check)
        self.act_break.triggered.connect(self.editor.toggle_breakpoint_at_caret)
        self.act_compile.triggered.connect(self.on_compile)
        self.act_pseudocode.triggered.connect(self.on_pseudocode)
        self.act_settings.triggered.connect(self.on_settings)

    def _request_input(self):
        input_text, ok = QInputDialog.getText(self, "Input Required",
                                              "Enter input for ',' command:")
        if ok:
            return input_text
        return ""

    def _on_mode_changed(self, button):
        mode_id = button.group().id(button)
        self.execution_mode = mode_id

        mode_names = ["Debug", "Slow (2/sec)", "Fast"]
        self.status.showMessage(f"{mode_names[mode_id]} mode enabled", 2000)

        if self.timer.isActive():
            self.timer.setInterval(self.timer_intervals[self.execution_mode])

    def _update_button_states(self):
        running = self.timer.isActive()
        paused = self.paused_at_breakpoint

        self.btn_run.setEnabled(not running and not paused)
        self.btn_step.setEnabled(not running)
        self.btn_pause.setEnabled(running and not paused)
        self.btn_resume.setVisible(paused)
        self.btn_reset.setEnabled(True)

    def on_run(self):
        if not self.interp.running:
            self._load_interpreter_from_ui()

        self.paused_at_breakpoint = False
        self.timer.setInterval(self.timer_intervals[self.execution_mode])
        self.timer.start()
        self._update_button_states()

    def on_step(self):
        if not self.interp.running and self.interp.pc == 0:
            self._load_interpreter_from_ui()

        self.timer.stop()
        self.paused_at_breakpoint = False

        self._execute_debug_step()
        self._update_button_states()

    def on_pause(self):
        self.timer.stop()
        self.paused_at_breakpoint = False
        self._update_button_states()

    def on_resume(self):
        self.paused_at_breakpoint = False
        self.timer.setInterval(self.timer_intervals[self.execution_mode])
        self.timer.start()
        self._update_button_states()

    def on_reset(self):
        self.timer.stop()
        self.paused_at_breakpoint = False
        self.interp.reset()
        # Reapply settings after reset
        self.interp.configure(self.settings['pointer_behavior'], self.settings['cell_wrap'])
        self.output.setPlainText("")
        self._update_status()
        self._refresh_memory()
        self.editor.update_highlighting(None)
        self._update_button_states()

    def on_open(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open Brainfuck file", "", "Brainfuck (*.bf *.b);;All Files (*)")
        if path:
            with open(path, 'r', encoding='utf-8') as f:
                self.editor.setPlainText(f.read())

    def on_save(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save Brainfuck file", "program.bf",
                                              "Brainfuck (*.bf *.b);;All Files (*)")
        if path:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(self.editor.toPlainText())

    def on_check(self):
        program = self.editor.toPlainText()
        temp_interp = Interpreter()
        temp_interp.loadProgram(program, "")
        errors = temp_interp.checkProgramSyntax()
        if not errors:
            QMessageBox.information(self, "Syntax", "No syntax errors detected.")
        else:
            msg = "\n".join([f"pos {i}: {repr(ch)}" for i, ch in errors[:200]])
            QMessageBox.warning(self, "Syntax", f"Found {len(errors)} issue(s):\n{msg}")

    def on_settings(self):
        dialog = SettingsDialog(self)
        dialog.set_pointer_behavior(self.settings['pointer_behavior'])
        dialog.set_cell_wrap(self.settings['cell_wrap'])

        if dialog.exec() == QDialog.Accepted:
            # Update settings
            self.settings['pointer_behavior'] = dialog.get_pointer_behavior()
            self.settings['cell_wrap'] = dialog.get_cell_wrap()

            # Apply to interpreter
            self.interp.configure(self.settings['pointer_behavior'], self.settings['cell_wrap'])

            # Show confirmation
            behavior_names = {
                PointerBehavior.CLAMP: "Clamp",
                PointerBehavior.WRAP: "Wrap-around",
                PointerBehavior.ERROR: "Error on overflow"
            }
            behavior_name = behavior_names[self.settings['pointer_behavior']]
            cell_mode = "wrap" if self.settings['cell_wrap'] else "no wrap"

            self.status.showMessage(f"Settings updated: Pointer={behavior_name}, Cells={cell_mode}", 3000)

    def on_compile(self):
        program = self.editor.toPlainText()
        temp_interp = Interpreter()
        temp_interp.loadProgram(program, "")
        if not hasattr(temp_interp, 'compileProgram'):
            QMessageBox.information(self, "Compilation",
                                    "This interpreter does not support compilation analysis.\n"
                                    "Please update your interpreter with the compileProgram method.")
            return

        try:
            compiled = temp_interp.compileProgram()
            original_ops = len([c for c in program if c in '[].,<>+-'])
            compiled_ops = len(compiled)

            optimizations = 0
            for cmd, arg in compiled:
                if cmd in ('+', '-', '<', '>') and arg and arg > 1:
                    optimizations += arg - 1

            efficiency = (optimizations / original_ops * 100) if original_ops > 0 else 0

            info = f"Original operations: {original_ops}\n"
            info += f"Compiled operations: {compiled_ops}\n"
            info += f"Operations saved by optimization: {optimizations}\n"
            info += f"Efficiency improvement: {efficiency:.1f}%\n\n"
            info += "Compiled instructions:\n"
            info += "-" * 40 + "\n"

            for i, (cmd, arg) in enumerate(compiled):
                if arg is None:
                    info += f"{i:3}: {cmd}\n"
                else:
                    info += f"{i:3}: {cmd} {arg}\n"

            jump_pairs = [(i, cmd, arg) for i, (cmd, arg) in enumerate(compiled) if cmd in '[]']
            if jump_pairs:
                info += f"\nJump table ({len(jump_pairs)} pairs):\n"
                info += "-" * 40 + "\n"
                for i, cmd, target in jump_pairs:
                    if target is not None:
                        info += f"{i:3}: {cmd} -> {target}\n"
                    else:
                        info += f"{i:3}: {cmd} (unresolved)\n"

            dialog = CompileOutputDialog(self, "Compiled Program Analysis", info)
            dialog.exec()

        except Exception as e:
            QMessageBox.warning(self, "Compilation Error", f"Error compiling program: {str(e)}")

    def on_pseudocode(self):
        program = self.editor.toPlainText()
        temp_interp = Interpreter()
        temp_interp.loadProgram(program, "")

        if not hasattr(temp_interp, 'generatePseudocode'):
            pseudocode = self._generate_pseudocode_fallback(program)
        else:
            try:
                pseudocode = temp_interp.generatePseudocode()
            except Exception as e:
                QMessageBox.warning(self, "Pseudocode Error", f"Error generating pseudocode: {str(e)}")
                return

        dialog = CompileOutputDialog(self, "Generated Pseudocode", pseudocode)
        dialog.exec()

    def _generate_pseudocode_fallback(self, program):
        pseudocode = f"Program loaded with {len(program)} characters.\n"
        pseudocode += f"Memory initialized with 30000 cells.\n"
        pseudocode += f"Pointer initialized at position 0.\n"
        pseudocode += f"pointer = 0\n\n"

        pointer = 0
        pc = 0
        tabber = ""

        while pc < len(program):
            char = program[pc]
            match char:
                case '>':
                    pointer += 1
                    pseudocode += f"{tabber}pointer++ ({pointer})\n"
                case '<':
                    pointer -= 1
                    pseudocode += f"{tabber}pointer-- ({pointer})\n"
                case '+':
                    pseudocode += f"{tabber}memory[pointer] += 1 (mod 256)\n"
                case '-':
                    pseudocode += f"{tabber}memory[pointer] -= 1 (mod 256)\n"
                case '.':
                    pseudocode += f"{tabber}print(char(memory[pointer]))\n"
                case ',':
                    pseudocode += f"{tabber}memory[pointer] = input_char()\n"
                case '[':
                    pseudocode += f"{tabber}while memory[pointer] != 0:\n"
                    tabber += "  "
                case ']':
                    tabber = tabber[:-2] if len(tabber) >= 2 else ""
                    pseudocode += f"{tabber}end while\n"
            pc += 1

        return pseudocode

    def _load_interpreter_from_ui(self):
        program = self.editor.toPlainText()
        self.interp.reset()
        self.interp.loadProgram(program, "")
        # Reapply settings after reset
        self.interp.configure(self.settings['pointer_behavior'], self.settings['cell_wrap'])
        if hasattr(self.interp, 'setInputCallback'):
            self.interp.setInputCallback(self._request_input)
        self.output.setPlainText("")
        should_highlight = (self.execution_mode == 0) or (not self.timer.isActive())
        self.editor.update_highlighting(self.interp.pc if should_highlight else None)

    def _execute_one_step(self):
        if self.execution_mode == 2 and hasattr(self.interp, 'runProgramFastInterruptible'):
            return self._execute_fast_chunk()
        else:
            return self._execute_debug_step()

    def _execute_fast_chunk(self):
        try:
            # Check for breakpoint at current position
            if self.interp.pc in self.editor.breakpoint_indices:
                self.timer.stop()
                self.paused_at_breakpoint = True
                self._update_button_states()
                self._update_ui_after_step()
                self.status.showMessage("Paused at breakpoint", 3000)
                return False

            more_needed = self.interp.runProgramFastInterruptible(steps_per_chunk=50000)

            if not more_needed:
                self.timer.stop()
                self._update_button_states()

            self._update_ui_after_step()
            return more_needed

        except PointerOverflowError as e:
            self.timer.stop()
            self.paused_at_breakpoint = False
            self._update_button_states()
            QMessageBox.critical(self, "Pointer Overflow", f"Pointer overflow error: {str(e)}")
            return False
        except Exception as e:
            self.timer.stop()
            self.paused_at_breakpoint = False
            self._update_button_states()
            QMessageBox.critical(self, "Runtime Error", f"Execution error: {str(e)}")
            return False

    def _execute_debug_step(self):
        if (self.timer.isActive() and
                self.interp.pc in self.editor.breakpoint_indices and
                not self.paused_at_breakpoint):
            self.timer.stop()
            self.paused_at_breakpoint = True
            self._update_button_states()
            self._update_ui_after_step()
            self.status.showMessage("Paused at breakpoint", 3000)
            return False

        if (self.interp.pc < len(self.interp.program) and
                self.interp.program[self.interp.pc] == ','):
            # Handle input command
            needs_input = False
            try:
                if hasattr(self.interp, 'input_buffer'):
                    if not self.interp.input_buffer:
                        needs_input = True
                else:
                    needs_input = True

                if needs_input:
                    # Stop execution to get input
                    was_running = self.timer.isActive()
                    self.timer.stop()
                    self.paused_at_breakpoint = False
                    self._update_button_states()

                    input_text = self._request_input()

                    if not input_text:
                        return False

                    input_chars = [ord(c) for c in input_text]

                    if hasattr(self.interp, 'input_buffer'):
                        self.interp.input_buffer = input_chars
                    else:
                        # Fallback for older interpreter versions
                        self.interp.input_buffer = input_chars

                    try:
                        advanced = self.interp.step()
                        self._update_ui_after_step()

                        if was_running and advanced:
                            self.timer.start()
                            self._update_button_states()

                        return advanced

                    except PointerOverflowError as e:
                        QMessageBox.critical(self, "Pointer Overflow", f"Pointer overflow error: {str(e)}")
                        return False
                    except Exception as e:
                        QMessageBox.critical(self, "Runtime Error", f"Execution error: {str(e)}")
                        return False

            except Exception as pre_check_error:
                print(f"Pre-check error: {pre_check_error}")

        try:
            advanced = self.interp.step()
            self._update_ui_after_step()

            if not advanced:
                self.timer.stop()
                self.paused_at_breakpoint = False
                self._update_button_states()

            return advanced

        except PointerOverflowError as e:
            self.timer.stop()
            self.paused_at_breakpoint = False
            self._update_button_states()
            QMessageBox.critical(self, "Pointer Overflow", f"Pointer overflow error: {str(e)}")
            return False
        except Exception as e:
            self.timer.stop()
            self.paused_at_breakpoint = False
            self._update_button_states()
            QMessageBox.critical(self, "Runtime Error", f"Execution error: {str(e)}")
            return False

    def _update_ui_after_step(self):
        try:
            current_output = str(self.interp.output_buffer)
            if self.output.toPlainText() != current_output:
                self.output.setPlainText(current_output)
                self.output.moveCursor(QTextCursor.End)
        except Exception as output_error:
            print(f"Output update error: {output_error}")

        try:
            self._update_status()
            self._refresh_memory()

            should_highlight = (self.execution_mode != 2) or self.paused_at_breakpoint or (not self.timer.isActive())
            if should_highlight:
                self.editor.update_highlighting(self.interp.pc)
            else:
                self.editor.update_highlighting(None)
        except Exception as ui_error:
            print(f"UI update error: {ui_error}")

    def _on_timer(self):
        if self.execution_mode == 2 and hasattr(self.interp, 'runProgramFastInterruptible'):
            # Fast mode with optimized execution
            if not self._execute_fast_chunk():
                self.timer.stop()
                self._update_button_states()
        else:
            # Debug/slow mode with step-by-step execution
            steps_per_tick = 1 if self.execution_mode == 1 else 10

            for _ in range(steps_per_tick):
                if not self.interp.running:
                    self.timer.stop()
                    self._update_button_states()
                    break

                if not self._execute_debug_step():
                    break

                if not self.timer.isActive():
                    break

    def _refresh_memory(self):
        center = self.interp.pointer

        total_rows = (self.interp.memory_size + 15) // 16
        visible_rows = min(32, total_rows)

        center_row = center // 16
        start_row = max(0, center_row - visible_rows // 2)
        end_row = min(total_rows, start_row + visible_rows)

        if end_row - start_row < visible_rows:
            start_row = max(0, end_row - visible_rows)

        self.mem_table.setRowCount(end_row - start_row)

        row_labels = []
        for i in range(end_row - start_row):
            addr = (start_row + i) * 16
            row_labels.append(f"{addr:04X}")
        self.mem_table.setVerticalHeaderLabels(row_labels)

        for row in range(end_row - start_row):
            for col in range(16):
                addr = (start_row + row) * 16 + col
                if addr < self.interp.memory_size:
                    item = QTableWidgetItem(str(self.interp.memory[addr]))

                    if addr == center:
                        item.setBackground(QColor(0, 100, 0))
                        item.setForeground(QColor(255, 255, 255))
                    else:
                        item.setBackground(QColor(255, 255, 255))
                        item.setForeground(QColor(0, 0, 0))
                else:
                    # Address beyond memory size
                    item = QTableWidgetItem("--")
                    item.setBackground(QColor(240, 240, 240))
                    item.setForeground(QColor(128, 128, 128))

                self.mem_table.setItem(row, col, item)

        current_row = center // 16 - start_row
        if 0 <= current_row < self.mem_table.rowCount():
            self.mem_table.scrollToItem(self.mem_table.item(current_row, center % 16))

        self.mem_table.resizeColumnsToContents()

        max_width = max(self.mem_table.columnWidth(i) for i in range(16))
        for i in range(16):
            self.mem_table.setColumnWidth(i, max_width)

    def _update_status(self):
        mode_names = ["Debug", "Slow", "Fast"]
        mode = mode_names[self.execution_mode]

        status_parts = [f"[{mode}]"]
        status_parts.append(f"pc={self.interp.pc}")
        status_parts.append(f"ptr={self.interp.pointer}")
        status_parts.append(f"mem[ptr]={self.interp.memory[self.interp.pointer]}")
        status_parts.append(f"running={'yes' if self.interp.running else 'no'}")

        if self.paused_at_breakpoint:
            status_parts.append("PAUSED AT BREAKPOINT")

        if hasattr(self.interp, '_fast_steps'):
            status_parts.append(f"steps={self.interp._fast_steps}")

        # Add settings info
        behavior_names = {
            PointerBehavior.CLAMP: "CLAMP",
            PointerBehavior.WRAP: "WRAP",
            PointerBehavior.ERROR: "ERROR"
        }
        behavior = behavior_names[self.settings['pointer_behavior']]
        cell_mode = "WRAP" if self.settings['cell_wrap'] else "NO-WRAP"
        status_parts.append(f"ptr-mode={behavior}")
        status_parts.append(f"cell-mode={cell_mode}")

        self.status.showMessage("  ".join(status_parts))

    def _load_sample(self):
        sample = (
            "++++++++++[>+++++++>++++++++++>+++>+<<<<-]>++.>+.+++++++..+++.>++.<<+++++++++++++++.>.+++.------.--------.>+.>."
        )
        self.editor.setPlainText(sample)
        self.interp.reset()
        self.interp.loadProgram(self.editor.toPlainText(), "")
        # Apply settings to sample
        self.interp.configure(self.settings['pointer_behavior'], self.settings['cell_wrap'])
        if hasattr(self.interp, 'setInputCallback'):
            self.interp.setInputCallback(self._request_input)
        self.interp.running = False
        self.editor.update_highlighting(self.interp.pc)
        self._refresh_memory()
        self._update_status()
        self._update_button_states()


def main():
    app = QApplication([])
    w = MainWindow()
    w.show()
    return app.exec()


if __name__ == '__main__':
    raise SystemExit(main())