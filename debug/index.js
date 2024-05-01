// SPDX-FileCopyrightText: Florian Wilhelm
// SPDX-License-Identifier: MIT

import { $ } from 'execa';

const matrix = {
    'debian': ['latest', 'testing', 'unstable'],
    'ubuntu': ['latest', 'rolling', 'devel'],
    'fedora': ['latest', 'rawhide']
}

const distros = Object.keys(matrix)

const images = distros.flatMap(distro => matrix[distro].map(tag => `${distro}:${tag}`))
console.log(images)

const pulls = images.map(image => $`docker pull ${image}`)
await Promise.all(pulls)

const builds = distros.flatMap(distro => matrix[distro].map(tag => $`docker build --file=Dockerfile.${distro} --build-arg=VERSION=${tag} --tag=debug-${distro}:${tag} .`))
await Promise.all(builds)

const runs = images.map(image => $`docker run -t --rm -v ${process.cwd()}:/debug debug-${image}`)
const processes = await Promise.all(runs)

processes.forEach(p => console.log(p.stdout))