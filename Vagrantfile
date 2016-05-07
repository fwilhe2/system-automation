Vagrant.configure(2) do |config|
  #config.vm.box = "box-cutter/fedora23"
  config.vm.box = "brodriguesneto/ubuntu-16.04-server"

  #config.vm.provision "shell", inline: "dnf install --assumeyes python python-dnf"
  config.vm.provision "shell", inline: "DEBIAN_FRONTEND=noninteractive apt-get update -q && apt-get install -yq python"

  config.vm.provision "ansible" do |ansible|
      ansible.playbook = "fedora.yml"
      ansible.raw_arguments = [
          '--verbose'
      ]
  end
end
