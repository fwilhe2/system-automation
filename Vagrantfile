Vagrant.configure(2) do |config|
  config.vm.box = "box-cutter/fedora23"

  config.vm.provision "shell",
      inline: "dnf install --assumeyes python python-dnf"

  config.vm.provision "ansible" do |ansible|
      ansible.playbook = "fedora.yml"
      ansible.raw_arguments = [
          '--verbose'
      ]
  end
end
