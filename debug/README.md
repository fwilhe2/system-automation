<!-- SPDX-FileCopyrightText: Florian Wilhelm
SPDX-License-Identifier: MIT -->

Local debugging setup.

Uses [execa](https://github.com/sindresorhus/execa/blob/main/docs/scripts.md) for scripting.

```
npm ci
NODE_DEBUG=execa node index.js | grep 'ok='
```