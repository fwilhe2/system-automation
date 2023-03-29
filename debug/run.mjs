#!/usr/bin/env zx

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

const runs = images.map(image => $`docker run -t --rm -v $PWD:/debug debug-${image}`)
await Promise.all(runs)