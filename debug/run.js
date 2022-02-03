const { spawn } = require('child_process');

const matrix = {
    'debian': ['latest', 'testing', 'unstable'],
    'ubuntu': ['latest', 'rolling', 'devel']
}

function runCommand(command, args) {
    console.log(`> ${command} ${args.toString()}`)
    const cmd = spawn(command, args)


    cmd.stdout.on('data', (data) => {
        console.log(`stdout: ${data}`);
    });

    cmd.stderr.on('data', (data) => {
        console.error(`stderr: ${data}`);
    });

    cmd.on('close', (code) => {
        console.log(`child process exited with code ${code}`);
    });
}

Object.keys(matrix).forEach(distro => {
    const tags = matrix[distro]

    tags.forEach(tag => {
        console.log(`=== PULL  ${distro}:${tag}`)
        runCommand('docker', ['pull', `${distro}:${tag}`])
    })

    tags.forEach(tag => {
        console.log(`=== BUILD  ${distro}:${tag}`)
        runCommand('docker', ['build', `--build-arg=DISTRO=${distro}`, `--build-arg=VERSION=${tag}`, `--tag=debug-${distro}:${tag}`, '.'])

    })

    tags.forEach(tag => {
        console.log(`=== RUN  ${distro}:${tag}`)
        runCommand('docker', ['run', '-t', '--rm', '-v', '$PWD:/debug', `debug-${distro}:${tag}`])
    })
})
