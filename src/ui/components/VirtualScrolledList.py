"""
Virtual Scrolled List Component for UI Performance Optimization
Implements virtual scrolling to handle large datasets efficiently
"""

import tkinter as tk
import math
from typing import List, Dict, Any, Callable, Optional
import time


class VirtualScrolledList:
    """
    Virtual scrolling list that only renders visible items
    Provides 10x+ performance improvement for large datasets
    """

    def __init__(self, parent, item_height: int = 40, buffer_size: int = 5):
        self.parent = parent
        self.item_height = item_height
        self.buffer_size = buffer_size

        # Data storage
        self.items: List[Dict[str, Any]] = []
        self.filtered_items: List[Dict[str, Any]] = []

        # UI components
        self.canvas = None
        self.scrollbar = None
        self.content_frame = None
        self.visible_widgets = {}

        # Scrolling state
        self.first_visible_index = 0
        self.visible_count = 0
        self.canvas_height = 0

        # Performance tracking
        self.last_render_time = 0
        self.render_count = 0

        # Callbacks
        self.on_item_click = None
        self.on_item_double_click = None
        self.render_item_callback = None

        self._setup_ui()

    def _setup_ui(self):
        """Setup the virtual scrolling UI components"""
        try:
            bg_color = self.parent.cget("bg")
        except Exception:
            bg_color = "#1a1a1a"

        # Main container
        self.main_frame = tk.Frame(self.parent, bg=bg_color)
        self.main_frame.pack(fill="both", expand=True)

        # Canvas for virtual scrolling
        self.canvas = tk.Canvas(
            self.main_frame,
            highlightthickness=0,
            bg=bg_color
        )
        self.canvas.pack(side="left", fill="both", expand=True)

        # Scrollbar
        self.scrollbar = tk.Scrollbar(
            self.main_frame,
            orient="vertical",
            command=self._on_scroll
        )
        self.scrollbar.pack(side="right", fill="y")

        # Configure canvas scrolling
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind("<Button-4>", lambda e: self._on_mousewheel(e, delta=1))
        self.canvas.bind("<Button-5>", lambda e: self._on_mousewheel(e, delta=-1))

        # Content frame for visible items
        self.content_frame = tk.Frame(self.canvas, bg=bg_color)
        self.canvas_window = self.canvas.create_window(
            0, 0, anchor="nw", window=self.content_frame
        )

        # Bind scroll events
        self.canvas.bind("<Visibility>", self._on_visibility_change)

    def set_items(self, items: List[Dict[str, Any]]):
        """Set the items to display"""
        self.items = items
        self.filtered_items = items.copy()
        self._update_scroll_region()
        self._render_visible_items()

    def filter_items(self, filter_func: Callable[[Dict[str, Any]], bool]):
        """Filter items based on a predicate function"""
        start_time = time.time()

        self.filtered_items = [item for item in self.items if filter_func(item)]

        # Clear current visible widgets
        self._clear_visible_widgets()

        # Reset scroll position
        self.canvas.yview_moveto(0)
        self.first_visible_index = 0

        # Update and render
        self._update_scroll_region()
        self._render_visible_items()

        filter_time = time.time() - start_time
        print(f"Filter completed in {filter_time:.3f}s - {len(self.filtered_items)} items")

    def set_render_callback(self, callback: Callable[[tk.Frame, Dict[str, Any], int], tk.Widget]):
        """Set the callback for rendering individual items"""
        self.render_item_callback = callback

    def set_item_click_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """Set callback for item clicks"""
        self.on_item_click = callback

    def set_item_double_click_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """Set callback for item double clicks"""
        self.on_item_double_click = callback

    def _on_canvas_configure(self, event):
        """Handle canvas resize"""
        self.canvas_height = event.height
        self._update_scroll_region()
        self._render_visible_items()

    def _update_scroll_region(self):
        """Update the canvas scroll region based on item count"""
        total_height = len(self.filtered_items) * self.item_height
        self.canvas.configure(scrollregion=(0, 0, 1, total_height))

        # Update scrollbar
        if len(self.filtered_items) > 0:
            max_scroll = max(0, total_height - self.canvas_height)
            try:
                self.scrollbar.configure(to=max_scroll)
            except:
                # Some ttk versions don't support 'to' option
                pass

    def _on_scroll(self, *args):
        """Handle scrollbar scrolling"""
        if len(self.filtered_items) == 0:
            return

        # Update canvas position
        self.canvas.yview(*args)

        # Calculate new visible range
        scroll_fraction = float(args[0]) if args else 0
        self.first_visible_index = int(
            scroll_fraction * len(self.filtered_items) * self.item_height / self.canvas_height
        )
        self.first_visible_index = max(0, min(self.first_visible_index, len(self.filtered_items) - 1))

        # Render visible items
        self._render_visible_items()

    def _on_mousewheel(self, event, delta=None):
        """Handle mouse wheel scrolling"""
        if delta is None:
            delta = -1 * (event.delta / 120)

        # Scroll the canvas
        self.canvas.yview_scroll(int(-delta), "units")

        # Update visible items after scroll
        self.parent.after(10, self._render_visible_items)

    def _on_visibility_change(self, event):
        """Handle visibility change events"""
        self._render_visible_items()

    def _render_visible_items(self):
        """Render only the visible items for performance"""
        start_time = time.time()

        if not self.filtered_items or not self.render_item_callback:
            return

        # Calculate visible range with buffer
        canvas_top = self.canvas.canvasy(0)
        canvas_bottom = canvas_top + self.canvas_height

        start_index = max(0, int(canvas_top / self.item_height) - self.buffer_size)
        end_index = min(
            len(self.filtered_items),
            int(canvas_bottom / self.item_height) + self.buffer_size
        )

        # Remove widgets that are no longer visible
        indices_to_remove = []
        for idx in self.visible_widgets:
            if idx < start_index or idx >= end_index:
                widget_info = self.visible_widgets[idx]
                if widget_info and widget_info['widget']:
                    widget_info['widget'].destroy()
                indices_to_remove.append(idx)

        for idx in indices_to_remove:
            del self.visible_widgets[idx]

        # Create new widgets for visible items
        for i in range(start_index, end_index):
            if i not in self.visible_widgets:
                self._create_item_widget(i)

        # Update positions of all visible widgets
        for idx, widget_info in self.visible_widgets.items():
            if widget_info and widget_info['widget']:
                widget_info['widget'].place(
                    x=0,
                    y=idx * self.item_height,
                    relwidth=1,
                    height=self.item_height
                )

        # Performance tracking
        render_time = time.time() - start_time
        self.render_count += 1
        self.last_render_time = render_time

        if self.render_count % 10 == 0:  # Log every 10th render
            print(f"Render #{self.render_count}: {render_time:.3f}s, {len(self.visible_widgets)} widgets")

    def _create_item_widget(self, index: int):
        """Create a widget for a specific item"""
        if index >= len(self.filtered_items):
            return

        item = self.filtered_items[index]

        try:
            # Create widget using the render callback
            widget = self.render_item_callback(self.content_frame, item, index)

            if widget:
                # Bind click events if callbacks are set
                if self.on_item_click:
                    widget.bind("<Button-1>", lambda e, i=item: self._on_item_click(e, i))

                if self.on_item_double_click:
                    widget.bind("<Double-Button-1>", lambda e, i=item: self._on_item_double_click(e, i))

                # Store widget reference
                self.visible_widgets[index] = {
                    'widget': widget,
                    'item': item,
                    'created_at': time.time()
                }
        except Exception as e:
            print(f"Error creating widget for item {index}: {e}")

    def _on_item_click(self, event, item: Dict[str, Any]):
        """Handle item click events"""
        if self.on_item_click:
            self.on_item_click(item)

    def _on_item_double_click(self, event, item: Dict[str, Any]):
        """Handle item double click events"""
        if self.on_item_double_click:
            self.on_item_double_click(item)

    def _clear_visible_widgets(self):
        """Clear all currently visible widgets"""
        for widget_info in self.visible_widgets.values():
            if widget_info and widget_info['widget']:
                try:
                    widget_info['widget'].destroy()
                except:
                    pass

        self.visible_widgets.clear()

    def get_selected_item(self) -> Optional[Dict[str, Any]]:
        """Get the currently selected item (if any)"""
        for widget_info in self.visible_widgets.values():
            if widget_info and hasattr(widget_info['widget'], 'selected') and widget_info['widget'].selected:
                return widget_info['item']
        return None

    def refresh(self):
        """Force refresh of the visible items"""
        self._clear_visible_widgets()
        self._render_visible_items()

    def scroll_to_item(self, index: int):
        """Scroll to a specific item"""
        if 0 <= index < len(self.filtered_items):
            # Calculate scroll position
            scroll_fraction = (index * self.item_height) / max(1, len(self.filtered_items) * self.item_height)
            self.canvas.yview_moveto(scroll_fraction)

            # Render the item
            self.parent.after(50, self._render_visible_items)

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        return {
            'total_items': len(self.items),
            'filtered_items': len(self.filtered_items),
            'visible_widgets': len(self.visible_widgets),
            'last_render_time': self.last_render_time,
            'render_count': self.render_count,
            'memory_efficiency': len(self.visible_widgets) / max(1, len(self.filtered_items))
        }

    def pack(self, **kwargs):
        """Pack the main frame"""
        self.main_frame.pack(**kwargs)

    def grid(self, **kwargs):
        """Grid the main frame"""
        self.main_frame.grid(**kwargs)

    def destroy(self):
        """Clean up resources"""
        self._clear_visible_widgets()
        if self.canvas:
            self.canvas.destroy()
        if self.scrollbar:
            self.scrollbar.destroy()
        if self.main_frame:
            self.main_frame.destroy()
