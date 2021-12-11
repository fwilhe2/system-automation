Vagrant.configure(2) do |config|
  config.vm.box = "f35-cloud-libvirt"
  config.vm.box_url = "https://mirror.23media.com/fedora/linux/releases/35/Cloud/x86_64/images/Fedora-Cloud-Base-Vagrant-35-1.2.x86_64.vagrant-libvirt.box"

  config.vm.provider 'libvirt' do |provider|
    provider.memory = 2048
    provider.cpus = 2
  end

  config.vm.provision "shell", inline: "sudo dnf -y install python3-dnf python3-libselinux"
  config.vm.provision "ansible" do |ansible|
      ansible.playbook = "common.yml"
      ansible.raw_arguments = [
          '--verbose'
      ]
  end
end
