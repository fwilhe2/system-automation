#!/usr/bin/env zx

const matrix = {
    'debian': ['latest', 'testing', 'unstable'],
    'ubuntu': ['latest', 'rolling', 'devel']
}

const distros = Object.keys(matrix)

const images = distros.flatMap(d => matrix[d].map(t => `${d}:${t}`))
console.log(images)
const pulls = images.map(i => $`docker pull ${i}`)
await Promise.all(pulls)
const builds = distros.flatMap(distro => matrix[distro].map(tag => $`docker build --build-arg=DISTRO=${distro} --build-arg=VERSION=${tag} --tag=debug-${distro}:${tag} .`))
await Promise.all(builds)
const runs = images.map(i => $`docker run -t --rm -v $PWD:/debug debug-${i}`)
await Promise.all(runs)