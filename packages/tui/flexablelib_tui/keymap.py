"""
CONFIGURABLE KEY MAP

A :class:`KeyMap` sits between the terminal and the application:

- ``remap`` renames incoming keys (``{'ctrl+j': 'down'}``: Ctrl+J moves down
  like the arrow), for terminals or people with other habits;
- ``actions`` names what keys do (``{'focus_next': ['tab'], 'quit':
  ['ctrl+q']}``), so :class:`~.app.App` and components ask for an action
  instead of hard-coding keys, and help screens can list them.

Key names are normalised (:func:`~.keys.normalize_key`), so ``'Ctrl+Shift+A'``,
``'control+A'`` and ``'ctrl+A'`` are the same key. Maps load from and save to
plain dictionaries or JSON files.

>>> km = KeyMap(remap={'ctrl+j': 'down'}, actions={'save': ['ctrl+s', 'F2']})
>>> km.action_for('f2')
'save'
>>> km.describe('save')
'Ctrl+S / F2'
"""

import json

from .keys import Key, key_label, normalize_key

__all__ = ['KeyMap', 'DEFAULT_ACTIONS']

#: Actions the application understands out of the box.
DEFAULT_ACTIONS = {
    'focus_next': ['tab'],
    'focus_prev': ['shift+tab'],
    'activate': ['enter', 'space'],
    'cancel': ['escape'],
    'quit': ['ctrl+c'],
    'help': ['f1'],
    'read_screen': ['ctrl+r'],
}


class KeyMap(object):
    """Key renames plus named actions (see the module docstring)."""

    def __init__(self, remap=None, actions=None, defaults=True):
        self.remap = {}
        self.actions = {}
        if defaults:
            for action, keys in DEFAULT_ACTIONS.items():
                self.bind(action, *keys)
        for src, dst in (remap or {}).items():
            self.remap[normalize_key(src)] = normalize_key(dst)
        for action, keys in (actions or {}).items():
            if isinstance(keys, str):
                keys = [keys]
            self.actions[action] = []
            self.bind(action, *keys)

    # -- editing ------------------------------------------------------------

    def bind(self, action, *keys):
        """Add keys to ``action`` (keeping the ones it has)."""
        bound = self.actions.setdefault(action, [])
        for key in keys:
            key = normalize_key(key)
            if key not in bound:
                bound.append(key)
        return self

    def unbind(self, action, *keys):
        """Remove keys from ``action`` (all of them without ``keys``)."""
        if not keys:
            self.actions.pop(action, None)
            return self
        drop = set(normalize_key(k) for k in keys)
        self.actions[action] = [k for k in self.actions.get(action, [])
                                if k not in drop]
        return self

    # -- lookups ------------------------------------------------------------

    def translate(self, key):
        """The key after ``remap`` (a :class:`Key`, extras preserved)."""
        target = self.remap.get(str(key))
        if target is None:
            return key
        if isinstance(key, Key):
            renamed = key.renamed(target)
            if len(target) == 1:
                renamed.char = target
            return renamed
        return Key(target, target if len(target) == 1 else '')

    def keys_for(self, action):
        return list(self.actions.get(action, []))

    def action_for(self, key):
        """The first action bound to ``key`` (``None`` if none)."""
        name = str(key)
        for action, keys in self.actions.items():
            if name in keys:
                return action
        return None

    def matches(self, key, action):
        return str(key) in self.actions.get(action, ())

    def describe(self, action, ascii=False, sep=' / '):
        """The keys of ``action`` as people read them: ``'Ctrl+S / F2'``."""
        return sep.join(key_label(k, ascii) for k in self.keys_for(action))

    def conflicts(self):
        """``{key: [actions]}`` for keys bound to more than one action."""
        seen = {}
        for action, keys in self.actions.items():
            for key in keys:
                seen.setdefault(key, []).append(action)
        return dict((k, v) for k, v in seen.items() if len(v) > 1)

    # -- persistence ----------------------------------------------------------

    def to_dict(self):
        return {'remap': dict(self.remap),
                'actions': dict((a, list(k)) for a, k in self.actions.items())}

    @classmethod
    def from_dict(cls, data, defaults=True):
        return cls(remap=data.get('remap'), actions=data.get('actions'),
                   defaults=defaults)

    @classmethod
    def load(cls, path, defaults=True):
        with open(path, encoding='utf-8') as handle:
            return cls.from_dict(json.load(handle), defaults)

    def save(self, path):
        with open(path, 'w', encoding='utf-8') as handle:
            json.dump(self.to_dict(), handle, ensure_ascii=False, indent=2)
