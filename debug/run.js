const { execSync } = require('child_process');

const matrix = {
    'debian': ['latest', 'testing', 'unstable'],
    'ubuntu': ['latest', 'rolling', 'devel']
}

function runCommand(command) {
    console.log(`> ${command}`)
    console.log(execSync(command).toString())
}

Object.keys(matrix).forEach(distro => {
    const tags = matrix[distro]

    console.log(`DISTRO: ${distro}`)
    tags.forEach(tag => {
        console.log(`TAG   : ${tag}`)
    })

    tags.forEach(tag => {
        console.log(`=== PULL  ${distro}:${tag}`)
        // runCommand('docker', ['pull', `${distro}:${tag}`])
        runCommand(`docker pull ${distro}:${tag}`)
    })

    tags.forEach(tag => {
        console.log(`=== BUILD  ${distro}:${tag}`)
        // runCommand('docker', ['build', `--build-arg=DISTRO=${distro}`, `--build-arg=VERSION=${tag}`, `--tag=debug-${distro}:${tag}`, '.'])
        runCommand(`docker build --build-arg=DISTRO=${distro} --build-arg=VERSION=${tag} --tag=debug-${distro}:${tag} .`)
    })

    tags.forEach(tag => {
        console.log(`=== RUN  ${distro}:${tag}`)
        // runCommand('docker', ['run', '-t', '--rm', '-v', '$PWD:/debug', `debug-${distro}:${tag}`])
        runCommand(`docker run -t --rm -v $PWD:/debug debug-${distro}:${tag}`)
    })
})
