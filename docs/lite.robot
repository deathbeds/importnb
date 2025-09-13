*** Settings ***
Library             Collections
Library             OperatingSystem
Library             Process
Library             SeleniumLibrary
Library             shutil

Suite Setup         Serve JupyterLite To Firefox
Suite Teardown      Stop Processes And Browsers


*** Variables ***
${HOST}                     127.0.0.1
${PORT}                     9999
${URL}                      http://${HOST}:${PORT}/
${LITE}                     %{PIXI_PROJECT_ROOT}${/}build${/}lite
${SCREENS}                  ${OUTPUT_DIR}${/}screens
${LOGS}                     ${OUTPUT_DIR}${/}logs
${_CSS_DISABLED}            .lm-mod-disabled
${_CSS_ENABLED}             :not(${_CSS_DISABLED})
${CSS_BODY}                 css:body
${CSS_SPINNER}              css:.jupyterlite-loading-indicator-spinner
${CSS_SPLASH}               css:#jupyterlab-splash
${CSS_LAUNCHER}             css:.jp-Launcher
${CSS_TREE_ITEM}            css:.jp-DirListing-item
${CSS_CMD_INPUT}            css:.lm-CommandPalette-input
${CSS_CMD_ITEM}             css:.lm-CommandPalette-item
${CSS_CMD_ITEM_ENABLED}     ${CSS_CMD_ITEM}${_CSS_ENABLED}
${CSS_KERNEL_STATUS}        css:.jp-KernelStatus
${CSS_KERNEL_IDLE}          css:.jp-KernelStatus-success
${CSS_ACCEPT_DIALOG}        css:.jp-Dialog-button.jp-mod-accept
${CSS_OUTPUT_STDERR}        css:[data-mime-type="application/vnd.jupyter.stderr"]
${CSS_CODE_CELL}            css:.jp-CodeCell


*** Test Cases ***
JupyterLite Opens
    Capture Page Screenshot    00-smoke${/}lite.png

A Notebook Can Be A Test Suite
    Restart And Run All Notebook    test_notebooks

A Notebook Can Be Code Docs
    Restart And Run All Notebook    docs_notebooks


*** Keywords ***
# main ############################################################################################
Restart And Run All Notebook
    [Arguments]    ${notebook}
    Reset App
    Set Screenshot Directory    ${SCREENS}${/}${notebook}
    Open File Tree Item    ${notebook}.ipynb
    Capture Page Screenshot    00-opening.png
    Wait For Idle Kernel
    Capture Page Screenshot    10-idle.png
    Run App Command    Run All Cells
    TRY
        Wait For Idle Kernel    60s
    FINALLY
        Capture All Elements    code-cells    ${CSS_CODE_CELL}
    END
    Notebook Should Have No Errors

# teardown ########################################################################################

Stop Processes And Browsers
    Terminate All Processes
    Close All Browsers

# setup ###########################################################################################

Serve JupyterLite To Firefox
    Create Directory    ${LOGS}
    Set Screenshot Directory    ${SCREENS}
    Start Process    python -m http.server -b ${HOST} ${PORT}
    ...    shell=${TRUE}
    ...    cwd=${LITE}
    ...    stdout=${LOGS}${/}lite.log.txt
    ...    stderr=STDOUT
    Open Firefox
    Go To    ${URL}
    Wait Until Page Contains Element    ${CSS_SPINNER}
    Wait Until Element Is Not Visible    ${CSS_SPINNER}
    Wait Until Element Is Not Visible    ${CSS_SPLASH}
    Wait Until Element Is Visible    ${CSS_LAUNCHER}

Open Firefox
    ${ff_options} =    Get Firefox Options
    ...    ui.prefersReducedMotion=${1}
    ...    devtools.console.stdout.content=${True}
    VAR    ${geckolog} =    ${LOGS}${/}geckodriver.log.txt
    VAR    ${geckolog} =    ${geckolog.replace('\\', '/')}
    ${gd} =    Which    geckodriver

    Open Browser
    ...    about:blank
    ...    headlessfirefox
    ...    options=${ff_options}
    ...    service=log_output='${geckolog}'; executable_path='${gd}'

Get Firefox Options
    [Arguments]    &{prefs}
    ${ff_options} =    Evaluate    selenium.webdriver.firefox.options.Options()
    ...    selenium.webdriver.firefox.options
    ${ff} =    Which    firefox
    VAR    ${ff_options.binary_location} =    ${ff}
    Set Firefox Preferences    ${ff_options}    &{prefs}
    RETURN    ${ff_options}

Set Firefox Preferences
    [Arguments]    ${ff_options}    &{prefs}
    FOR    ${pref}    ${value}    IN    &{prefs}
        Call Method    ${ff_options}    set_preference    ${pref}    ${value}
    END

# app #############################################################################################

Reset App
    Run App Command    Shut Down All Kernels    allow_missing=${TRUE}
    Run App Command    Close All Tabs
    Wait Until Element Is Visible    ${CSS_LAUNCHER}

Run App Command
    [Arguments]    ${command}    ${allow_missing}=${FALSE}
    Press Keys    ${CSS_BODY}    CTRL+SHIFT+c
    Input Text    ${CSS_CMD_INPUT}    ${command}
    ${els} =    Get WebElements    ${CSS_CMD_ITEM_ENABLED}
    IF    ${els.__len__()}
        Click Element    ${CSS_CMD_ITEM_ENABLED}
    ELSE IF    ${allow_missing}
        Press Keys    ${CSS_BODY}    ESC
    ELSE
        Page Should Contain Element    ${CSS_CMD_ITEM_ENABLED}
    END
    Wait Until Element Is Not Visible    ${CSS_CMD_INPUT}
    Sleep    0.3s
    Accept App Dialogs

Accept App Dialogs
    ${accepts} =    Get WebElements    ${CSS_ACCEPT_DIALOG}
    IF    ${accepts.__len__()}
        Click Element    ${CSS_ACCEPT_DIALOG}
        Wait Until Page Does Not Contain Element    ${CSS_ACCEPT_DIALOG}
    END

Notebook Should Have No Errors
    Capture All Elements    unexpected-stderr    ${CSS_OUTPUT_STDERR}    ${print_text}=${TRUE}
    Page Should Not Contain Element    ${CSS_OUTPUT_STDERR}

Open File Tree Item
    [Arguments]    ${filename}
    Double Click Element    ${CSS_TREE_ITEM}\[title^="Name: ${filename}"]

Wait For Idle Kernel
    [Arguments]    ${timeout}=30s
    Wait Until Element Is Visible    ${CSS_KERNEL_STATUS}
    Wait Until Element Is Visible    ${CSS_KERNEL_IDLE}    timeout=${timeout}

# capture #########################################################################################

Capture All Elements
    [Arguments]    ${stem}    ${selector}    ${ext}=png    ${print_text}=${FALSE}
    ${els} =    Get WebElements    ${selector}
    ${el_files} =    Create List
    FOR    ${i}    ${el}    IN ENUMERATE    @{els}
        ${i_just} =    Evaluate    "${i}".rjust(2, "0")
        VAR    ${screen} =    ${stem}-${i_just}-{index}.${ext}
        ${file} =    Capture Element Screenshot    ${el}    ${screen}
        IF    ${print_text}
            ${el_text} =    Get Text    ${el}
            Log    ${el_text}
        END
        Append To List    ${el_files}    ${file}
    END
    RETURN    ${el_files}
