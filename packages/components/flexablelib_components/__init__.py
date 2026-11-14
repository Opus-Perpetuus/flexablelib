"""
Interactive terminal components for flexablelib
(``pip install flexablelib[components]``).

Form inputs (text, password, numbers, arithmetic, money, masks, multi-line,
JSON, code scanners, checkboxes, switches, radio and checkbox groups, selects,
autocomplete, colours, icons, coordinates, files, signatures), dates, times
and stopwatches, display
pieces (badges, alerts, links, breadcrumbs, code, Markdown/HTML, timelines,
steppers, comments, stats, charts), navigation (tabs, menus, pagination,
sidebar, wizard, accordion, tree, command palette, split panes, app shell),
data (interactive and editable tables, filter bar, catalog, forms, login)
dialogs (modal, confirm, prompt, loading, popover) and pictures (image,
image viewer: kitty, iTerm2, sixel, Unicode blocks, ASCII, link).

Every component works inside :class:`flexablelib_tui.App` (focus with Tab,
keys to the focused component) and also renders on its own with
``render(width)``. See docs/COMPONENTS.md.
"""

__version__ = '3.7.0'

from .base import Theme, DEFAULT_THEME, Input, Box, Button, frame
from .inputs import (TextInput, PasswordInput, NumberInput, ExpressionInput,
                     MoneyInput, MaskedInput, MASKS, TextArea, JsonInput,
                     ScanInput, Checkbox, Switch, RadioGroup, CheckboxGroup,
                     Select, Autocomplete, ColorInput, IconPicker,
                     CoordinatesInput, FileInput, SignatureInput,
                     evaluate_expression, ICONS)
from .dates import (Calendar, DateInput, TimeInput, DateTimeInput, WeekInput,
                    MonthInput, YearInput, WeekdayInput, DateRangeInput,
                    Timer, Stopwatch)
from .display import (Badge, Tag, StatusBadge, Alert, Link, Breadcrumbs,
                      EmptyState, ErrorPanel, Spinner, Skeleton, Code,
                      MarkdownView, HtmlView, DetailView, Timeline, Stepper,
                      CommentList, AttachmentList, Stat, LineChart,
                      StatusLine, human_size)
from .navigation import (Tabs, Menu, ContextMenu, MenuButton, Pagination,
                         Sidebar, TopBar, Toolbar, Wizard, Accordion,
                         Carousel, Tree, CommandPalette, Split, Stack,
                         VStack, GridView, AppShell, SortControl)
from .data import (DataTable, FilterBar, EditableTable, CatalogGrid, Form,
                   FormCell, ValidationSummary, LoginForm, FilePreview, parse_query)
from .media import Image, ImageViewer, IMAGE_EXTENSIONS
from .overlays import (Modal, ConfirmDialog, PromptDialog, LoadingOverlay,
                       Popover, HelpLine)

__all__ = [
    'Theme', 'DEFAULT_THEME', 'Input', 'Box', 'Button', 'frame',
    'TextInput', 'PasswordInput', 'NumberInput', 'ExpressionInput',
    'MoneyInput', 'MaskedInput', 'MASKS', 'TextArea', 'JsonInput',
    'ScanInput', 'Checkbox', 'Switch', 'RadioGroup', 'CheckboxGroup',
    'Select', 'Autocomplete', 'ColorInput', 'IconPicker', 'CoordinatesInput',
    'FileInput', 'SignatureInput', 'evaluate_expression', 'ICONS',
    'Calendar', 'DateInput', 'TimeInput', 'DateTimeInput', 'WeekInput',
    'MonthInput', 'YearInput', 'WeekdayInput', 'DateRangeInput', 'Timer',
    'Stopwatch',
    'Badge', 'Tag', 'StatusBadge', 'Alert', 'Link', 'Breadcrumbs',
    'EmptyState', 'ErrorPanel', 'Spinner', 'Skeleton', 'Code',
    'MarkdownView', 'HtmlView', 'DetailView', 'Timeline', 'Stepper',
    'CommentList', 'AttachmentList', 'Stat', 'LineChart', 'StatusLine',
    'human_size',
    'Tabs', 'Menu', 'ContextMenu', 'MenuButton', 'Pagination', 'Sidebar',
    'TopBar', 'Toolbar', 'Wizard', 'Accordion', 'Carousel', 'Tree',
    'CommandPalette', 'Split', 'Stack', 'VStack', 'GridView', 'AppShell', 'SortControl',
    'DataTable', 'FilterBar', 'EditableTable', 'CatalogGrid', 'Form',
    'FormCell',
    'ValidationSummary', 'LoginForm', 'FilePreview', 'parse_query',
    'Modal', 'ConfirmDialog', 'PromptDialog', 'LoadingOverlay', 'Popover',
    'HelpLine', 'Image', 'ImageViewer', 'IMAGE_EXTENSIONS', '__version__',
]
