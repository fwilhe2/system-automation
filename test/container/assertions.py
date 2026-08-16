# SPDX-FileCopyrightText: Florian Wilhelm
# SPDX-License-Identifier: MIT
"""Assertions about the system the playbooks just set up.

Imported by run-test.py, which applies the playbooks first. Each assertion
exits the process with a message on the first failure.
"""

import json
import os
import pathlib
import platform
import re
import shutil
import subprocess
import sys
import urllib.request
import xml.etree.ElementTree

import yaml


def assert_equals(first, second, message):
    if not first == second:
        sys.exit(
            f"Assertion failed. '{first}' should equal '{second}', but did not. Message: {message}"
        )


def assert_true(val, message):
    if not val:
        sys.exit(
            f"Assertion failed. '{val}' should equal 'True', but did not. Message: {message}"
        )


def assert_not_none(value, message):
    if value is None:
        sys.exit(
            f"Assertion failed. '{value}' should not be 'None'. Message: {message}"
        )


def assert_system_properties():
    expected_binaries = {
        "javac": "-version",
        "mvn": "-version",
        "go": "version",
        "keepassxc-cli": "-version",
        "gcl": "--version",
    }

    for binary, version_argument in expected_binaries.items():
        binary_with_path = shutil.which(binary)
        if binary_with_path is None:
            sys.exit(f"Error: Could not find {binary}")
        print(f"Found binary for {binary} at '{binary_with_path}'")
        script = f"set -e && {binary_with_path} {version_argument}"
        assert_equals(
            subprocess.run(["bash", "-c", f"{script}"]).returncode,
            0,
            f"Expected {script} to run with exit code 0.",
        )


def assert_rust_toolchain():
    """Rust comes from rustup, installed with --no-modify-path, so nothing puts
    `~/.cargo/bin` on the PATH of this process and the binaries are called
    through their full path here."""
    cargo_bin = pathlib.Path.home() / ".cargo/bin"
    for binary in ("rustup", "cargo", "rustc"):
        executable = cargo_bin / binary
        assert_true(os.access(executable, os.X_OK),
                    f"Expected '{executable}' to be an executable rustup shim.")
        assert_equals(
            subprocess.run([str(executable), "--version"]).returncode, 0,
            f"Expected '{executable} --version' to run with exit code 0.")

    # rustup builds the toolchain name from the host triple, so a toolchain
    # installed for the wrong architecture would show up here.
    expected = f"stable-{platform.machine()}-unknown-linux-gnu"
    toolchains = subprocess.run([str(cargo_bin / "rustup"), "toolchain", "list"],
                                capture_output=True)
    installed = toolchains.stdout.decode("utf-8")
    assert_true(
        any(line.startswith(expected) for line in installed.splitlines()),
        f"Expected the '{expected}' toolchain, rustup has: {installed}")
    print(f"rustup: {expected} installed in {cargo_bin.parent}")


firefox_channels = {
    "devedition": "Firefox Developer",
    "nightly": "Firefox Nightly",
}


def read_from_archive(archive, path):
    # unzip exits 2 on the non-standard headers omni.ja uses, but still extracts
    # the file correctly, so the output is checked instead of the return code.
    result = subprocess.run(["unzip", "-p", str(archive), path], capture_output=True)
    assert_true(
        len(result.stdout) > 0,
        f"Expected to read '{path}' from '{archive}': {result.stderr.decode('utf-8')}",
    )
    return result.stdout.decode("utf-8")


def firefox_install(channel):
    return pathlib.Path(f"/opt/firefox/firefox-{channel}/firefox")


def installed_policies(channel):
    policies = firefox_install(channel) / "distribution/policies.json"
    return json.loads(policies.read_text())["policies"]


def firefox_role_defaults():
    """The role's own defaults, to check the generated policies against."""
    repository = pathlib.Path(__file__).resolve().parents[2]
    return yaml.safe_load(
        (repository / "roles/firefox/defaults/main.yml").read_text())


def javascript_string_list(source, name):
    """Read a `const name = ["a", "b"];` array out of a Firefox module."""
    match = re.search(rf"(?:const|let)\s+{name}\s*=\s*\[(.*?)\];", source, re.DOTALL)
    assert_not_none(
        match,
        f"Could not find '{name}' in Policies.sys.mjs. Firefox likely restructured "
        f"the preference allow list and this test needs to be updated.",
    )
    return re.findall(r'"([^"]+)"', match.group(1))


def elf_machine(binary):
    """Read e_machine out of an ELF header, without needing 'file' installed."""
    with open(binary, "rb") as elf:
        header = elf.read(20)
    assert_equals(header[:4], b"\x7fELF", f"Expected '{binary}' to be an ELF binary.")
    return int.from_bytes(header[18:20], "little")


def assert_preferences_are_settable(policies, source, display_name):
    """Firefox silently drops preferences it does not allow, and only reports
    them in about:policies, so they have to be checked up front."""
    allowed_prefixes = javascript_string_list(source, "allowedPrefixes")
    allowed_security_prefs = javascript_string_list(source, "allowedSecurityPrefs")
    blocked_prefs = javascript_string_list(source, "blockedPrefs")

    for preference in policies.get("Preferences", {}):
        if preference.startswith("security."):
            allowed = preference in allowed_security_prefs
        else:
            allowed = any(
                preference.startswith(prefix) for prefix in allowed_prefixes)
        assert_true(
            allowed and preference not in blocked_prefs,
            f"{display_name} refuses to set '{preference}' via the "
            f"Preferences policy. Use the dedicated policy for it instead.")


def assert_policy_values_are_valid(policies, schema, display_name):
    """The enums the schema spells out, for the two policies this role fills
    from configuration. A misspelled status or installation mode is not an
    error to Firefox, it just drops the entry."""
    statuses = allowed_values(
        single_pattern(schema["Preferences"])["properties"]["Status"])
    for preference, setting in policies.get("Preferences", {}).items():
        assert_true(
            setting["Status"] in statuses,
            f"'{setting['Status']}' of '{preference}' is not a preference "
            f"status {display_name} knows about, it accepts {statuses}.")

    # The catch-all "*" entry is described separately from the per-add-on ones,
    # and only the latter can install anything.
    addon_schema = single_pattern(schema["ExtensionSettings"])["properties"]
    modes = allowed_values(addon_schema["installation_mode"])
    # Without this key an add-on is disabled in private windows, which is every
    # window these channels open, so a Firefox that stopped honouring it would
    # leave the add-ons installed but never running.
    assert_true(
        "private_browsing" in addon_schema,
        f"{display_name} does not know a 'private_browsing' setting for "
        f"add-ons any more. Check how it now allows them in private windows.")

    for addon_id, settings in policies.get("ExtensionSettings", {}).items():
        assert_true(
            settings["installation_mode"] in modes,
            f"'{settings['installation_mode']}' of '{addon_id}' is not an "
            f"installation mode {display_name} knows about, it accepts {modes}.")
        assert_true(
            "install_url" in settings,
            f"'{addon_id}' has no install_url, so {display_name} has nowhere "
            f"to install it from.")


def allowed_values(value_schema):
    """The values a string-valued policy setting accepts. Firefox is in the
    middle of respelling these: the older channels list them in an 'enum', the
    newer ones as a 'oneOf' of documented 'const' entries."""
    if "enum" in value_schema:
        return value_schema["enum"]
    assert_true(
        "oneOf" in value_schema,
        f"Expected an 'enum' or a 'oneOf' in {value_schema}. Firefox "
        f"restructured the schema and this test needs to be updated.")
    return [alternative["const"] for alternative in value_schema["oneOf"]]


def single_pattern(policy_schema):
    """The sub-schema of a policy whose keys are user-chosen names."""
    patterns = list(policy_schema["patternProperties"].values())
    assert_equals(
        len(patterns), 1,
        f"Expected exactly one pattern in {policy_schema['patternProperties']}. "
        f"Firefox restructured the schema and this test needs to be updated.")
    return patterns[0]


def assert_policies_match_defaults(policies, defaults, display_name):
    """The template takes a preference either as a bare value or as a mapping
    that names a status, and an add-on with or without an installation mode, so
    both spellings are checked here. A preference that silently ends up locked
    greys out a working checkbox in the settings UI."""
    for name, preference in defaults["firefox_preferences"].items():
        expected = preference if isinstance(preference, dict) else {
            "value": preference
        }
        assert_true(
            name in policies["Preferences"],
            f"'{name}' is configured for the role but missing from the "
            f"policies of {display_name}.")
        generated = policies["Preferences"][name]
        assert_equals(generated["Value"], expected["value"],
                      f"Wrong value generated for preference '{name}'.")
        assert_equals(generated["Status"], expected.get("status", "locked"),
                      f"Wrong status generated for preference '{name}'.")

    for addon_id, addon in defaults["firefox_extensions"].items():
        assert_true(
            addon_id in policies["ExtensionSettings"],
            f"'{addon_id}' is configured for the role but missing from the "
            f"policies of {display_name}.")
        generated = policies["ExtensionSettings"][addon_id]
        assert_equals(generated["install_url"], addon["url"],
                      f"Wrong install_url generated for '{addon_id}'.")
        assert_equals(generated["installation_mode"],
                      addon.get("mode", "normal_installed"),
                      f"Wrong installation mode generated for '{addon_id}'.")
        assert_equals(generated["private_browsing"],
                      addon.get("private_browsing", True),
                      f"Wrong private browsing setting generated for '{addon_id}'.")


def assert_addon_ids_match_their_xpi():
    """The policy names the add-on it installs by ID, and Firefox rejects the
    install when the XPI declares a different one. The add-on ID and the AMO
    slug in the URL are picked independently of each other, so nothing but this
    check keeps the pair honest - and a mismatch is invisible until a browser
    starts up without the add-on."""
    for addon_id, settings in installed_policies("nightly").get(
            "ExtensionSettings", {}).items():
        xpi = pathlib.Path(f"/tmp/{addon_id}.xpi")
        request = urllib.request.Request(
            settings["install_url"],
            # addons.mozilla.org answers 403 to the default urllib agent.
            headers={"User-Agent": "system-automation-test"})
        with urllib.request.urlopen(request) as response:
            xpi.write_bytes(response.read())

        manifest = json.loads(read_from_archive(xpi, "manifest.json"))
        gecko = (manifest.get("browser_specific_settings")
                 or manifest.get("applications") or {}).get("gecko", {})
        assert_equals(
            gecko.get("id"), addon_id,
            f"The add-on behind '{settings['install_url']}' calls itself "
            f"'{gecko.get('id')}', so Firefox refuses to install it as "
            f"'{addon_id}'. Check the slug in the URL against the ID.")
        xpi.unlink()
        print(f"{addon_id}: served by {settings['install_url']}")


def assert_telemetry_opt_out():
    assert_true(
        "DO_NOT_TRACK=1" in pathlib.Path("/etc/environment").read_text().splitlines(),
        "Expected DO_NOT_TRACK=1 in '/etc/environment'.")

    mode = pathlib.Path.home() / ".config/go/telemetry/mode"
    assert_equals(mode.read_text().strip(), "off",
                  f"Expected Go telemetry to be off in '{mode}'.")

    print("Telemetry opt-out is in place")


def assert_spellcheck_locales():
    """Firefox and LibreOffice offer whatever hunspell dictionaries the system
    carries, so the set of files in these directories is the set of languages
    the spellchecker can be switched to."""
    installed = set()
    for directory in ("/usr/share/hunspell", "/usr/share/myspell",
                      "/usr/share/myspell/dicts"):
        path = pathlib.Path(directory)
        if not path.is_dir():
            continue
        # Hyphenation patterns share the directories and are not dictionaries.
        installed |= {
            entry.stem
            for entry in path.iterdir()
            if entry.suffix in (".aff", ".dic")
            and not entry.name.startswith("hyph_")
        }

    assert_equals(sorted(installed), ["de_DE", "en_US"],
                  "Expected exactly these spellcheck locales to be installed.")
    print("Spellcheck is limited to de_DE and en_US")


def assert_libreoffice_locale():
    """The locale settings the libreoffice role writes into the user profile.

    Skipped where LibreOffice is not packaged - the EL rebuilds dropped it,
    which is the same condition the role carries in the desktop playbook.
    """
    if shutil.which("soffice") is None:
        print("LibreOffice is not installed here, skipping")
        return

    repository = pathlib.Path(__file__).resolve().parents[2]
    defaults = yaml.safe_load(
        (repository / "roles/libreoffice/defaults/main.yml").read_text()
    )
    settings = defaults["libreoffice_locale_settings"]

    registry = pathlib.Path.home() / ".config/libreoffice/4/user/registrymodifications.xcu"
    items = xml.etree.ElementTree.parse(registry).getroot()
    oor = "{http://openoffice.org/2001/registry}"

    # The item path is matched in python rather than in the ElementPath
    # expression: the factory paths quote the factory itself, and a quote inside
    # a predicate literal is more than ElementPath's XPath subset can parse.
    def assert_fused(item_path, name, expected):
        prop = next(
            (found
             for item in items if item.get(f"{oor}path") == item_path
             for found in item.findall(f"prop[@{oor}name='{name}']")), None)
        assert_not_none(prop, f"Expected a '{name}' property in '{registry}'.")
        assert_equals(prop.get(f"{oor}op"), "fuse",
                      f"Expected '{name}' in '{registry}' to be fused.")
        assert_equals(prop.findtext("value"), expected,
                      f"Expected '{name}' in '{registry}' to be '{expected}'.")

    for name, expected in settings.items():
        assert_fused("/org.openoffice.Setup/L10N", name, expected)

    calc_filter = defaults["libreoffice_calc_default_filter"]
    assert_fused(
        "/org.openoffice.Setup/Office/Factories/org.openoffice.Setup:Factory"
        "['com.sun.star.sheet.SpreadsheetDocument']",
        "ooSetupFactoryDefaultFilter", calc_filter)

    print(f"LibreOffice is set up for {settings}, saving as '{calc_filter}'")


def assert_firefox_setup():
    home = pathlib.Path.home()
    defaults = firefox_role_defaults()
    # https://refspecs.linuxfoundation.org/elf/gabi4+/ch4.eheader.html
    expected_machine = {"x86_64": 0x3E, "aarch64": 0xB7}[platform.machine()]

    for channel, display_name in firefox_channels.items():
        install = firefox_install(channel)

        # Mozilla serves x86_64 unless the download URL asks for another
        # architecture, so a wrong URL yields a browser that cannot run here.
        assert_equals(
            elf_machine(install / "firefox"), expected_machine,
            f"{display_name} was built for a different architecture than "
            f"{platform.machine()}. Check the os= parameter of the download URL.")

        # Firefox opens the profile manager and waits forever when the --profile
        # directory does not exist, so its presence is what makes the browser
        # start unattended.
        profile = home / ".local/share/firefox-profiles" / channel
        assert_true(profile.is_dir(),
                    f"Expected profile directory '{profile}' for {display_name}.")
        assert_equals(
            oct(profile.stat().st_mode & 0o777), oct(0o700),
            f"Expected profile directory '{profile}' to be private.")

        entry = home / ".local/share/applications" / f"firefox-{channel}.desktop"
        assert_true(entry.is_file(),
                    f"Expected desktop entry '{entry}' for {display_name}.")
        exec_lines = [
            line for line in entry.read_text().splitlines()
            if line.startswith("Exec=")
        ]
        assert_true(len(exec_lines) > 0, f"Expected an Exec line in '{entry}'.")
        for exec_line in exec_lines:
            assert_true(
                f"--profile {profile}" in exec_line,
                f"Expected '{exec_line}' to start on profile '{profile}'.")
            # Opening in a private window is intentional for these channels.
            assert_true(" --private-window " in exec_line,
                        f"Expected '{exec_line}' to open a private window.")
            binary = pathlib.Path(exec_line.split(" ")[2])
            assert_true(os.access(binary, os.X_OK),
                        f"Expected '{binary}' from '{entry}' to be executable.")

        # Validate the generated policies against the rules of the very Firefox
        # build that was just installed, so this keeps working as Firefox
        # changes which policies and preferences it accepts.
        policies = installed_policies(channel)
        omni = install / "browser/omni.ja"

        schema = json.loads(
            read_from_archive(omni, "modules/policies/policies-schema.json"))
        for policy in policies:
            assert_true(
                policy in schema["properties"],
                f"'{policy}' is not a policy {display_name} knows about.")

        assert_preferences_are_settable(
            policies,
            read_from_archive(omni, "modules/policies/Policies.sys.mjs"),
            display_name)
        assert_policy_values_are_valid(policies, schema["properties"],
                                       display_name)
        assert_policies_match_defaults(policies, defaults, display_name)

        print(f"{display_name}: profile, desktop entry, "
              f"{len(policies['ExtensionSettings'])} add-ons, "
              f"{len(policies['Preferences'])} preferences and "
              f"{len(policies)} policies are valid")
