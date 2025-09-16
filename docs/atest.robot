*** Settings ***
Library             Collections
Library             OperatingSystem
Library             Process
Library             SeleniumLibrary
Library             shutil
Library             textwrap

Suite Setup         Serve JupyterLite
Suite Teardown      Suite Teardown
Test Setup          Test Setup
Test Teardown       Test Teardown


*** Variables ***
${LITE}                     %{PIXI_PROJECT_ROOT}${/}build${/}lite
${SCREENS}                  ${OUTPUT_DIR}${/}screens
${LOGS}                     ${OUTPUT_DIR}${/}logs
${DOWNLOADS}                ${OUTPUT_DIR}${/}downloads
${_CSS_DISABLED}            .lm-mod-disabled
${_CSS_ENABLED}             :not(${_CSS_DISABLED})
${_CSS_STDERR_MIME}         [data-mime-type="application/vnd.jupyter.stderr"]
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
${CSS_CELL}                 css:.jp-Cell
${CSS_CODE_CELL}            css:.jp-CodeCell
${CSS_CODE_CELL_ERROR}      ${CSS_CODE_CELL}:has(${_CSS_STDERR_MIME})
${CSS_MAIN_LOGO}            css:#jp-MainLogo
${LITE_URL}                 ${EMPTY}


*** Test Cases ***
JupyterLite Opens
    Capture Page Screenshot    00-opened.png

Notebook As Test
    Restart And Run All Notebook    test_notebooks

Notebook As API Docs
    Restart And Run All Notebook    docs_notebooks


*** Keywords ***
# main ############################################################################################
Restart And Run All Notebook
    [Arguments]    ${notebook}
    Open Notebook    ${notebook}
    Run App Command    Run All Cells
    Accept App Dialogs
    TRY
        Wait For Idle Kernel    80s
        Notebook Should Have No Errors
    FINALLY
        Capture Page Screenshot    20-restart-run-all.png
        Capture All Elements    30-code-cells    ${CSS_CODE_CELL}
        Download Notebook    ${notebook}
    END

# lifecycle ########################################################################################

Suite Setup
    Serve JupyterLite

Suite Teardown
    Terminate All Processes
    Close All Browsers

Test Teardown
    Close All Browsers

Test Setup
    VAR    ${stem} =    ${TEST_NAME.lower().replace(' ', '_')}
    Open Firefox    ${stem}
    Go To    ${LITE_URL}
    Set Screenshot Directory    ${SCREENS}${/}
    Wait For JupyterLite

# app #############################################################################################

Open Notebook
    [Arguments]    ${notebook}
    Open File Tree Item    ${notebook}.ipynb
    Capture Page Screenshot    00-opening.png
    Wait For Idle Kernel
    Capture Page Screenshot    10-idle.png
    Click Element    ${CSS_CELL}

Download Notebook
    [Arguments]    ${expect}=${EMPTY}
    Capture Page Screenshot    99-about-to-save.png
    Click Element    ${CSS_CODE_CELL}
    Run App Command    Save Notebook
    Capture Page Screenshot    99-clicked-cell.png
    Run App Command    Download
    IF    ${expect.__len__()}
        Wait Until Created    ${DOWNLOADS}${/}${expect}.ipynb    5s
    END

Run App Command
    [Arguments]    ${command}    ${allow_missing}=${FALSE}
    Press Keys    ${CSS_BODY}    CTRL+SHIFT+c
    Input Text    ${CSS_CMD_INPUT}    ${command}
    ${els} =    Get WebElements    ${CSS_CMD_ITEM_ENABLED}
    IF    ${els.__len__()}
        Click Element    ${CSS_CMD_ITEM_ENABLED}
    ELSE IF    ${allow_missing}
        Click Element    ${CSS_MAIN_LOGO}
    ELSE
        Page Should Contain Element    ${CSS_CMD_ITEM_ENABLED}
    END
    Sleep    0.3s
    Accept App Dialogs

Accept App Dialogs
    ${accepts} =    Get WebElements    ${CSS_ACCEPT_DIALOG}
    IF    ${accepts.__len__()}
        Click Element    ${CSS_ACCEPT_DIALOG}
        Wait Until Page Does Not Contain Element    ${CSS_ACCEPT_DIALOG}
    END

Notebook Should Have No Errors
    VAR    ${stem} =    unexpected-stderr
    Capture All Elements    ${stem}    css:${_CSS_STDERR_MIME}
    Log All Elements    ${CSS_CODE_CELL_ERROR}    ${stem}    ERROR
    Page Should Not Contain Element    ${CSS_CODE_CELL_ERROR}

Open File Tree Item
    [Arguments]    ${filename}
    VAR    ${sel} =    ${CSS_TREE_ITEM}\[title^="Name: ${filename}"]
    Wait Until Element Is Visible    ${sel}
    Capture Page Screenshot    DEBUG-{index}.png
    Double Click Element    ${sel}
    Capture Page Screenshot    DEBUG-{index}.png

Wait For Idle Kernel
    [Arguments]    ${timeout}=30s
    Wait Until Element Is Visible    ${CSS_KERNEL_STATUS}
    Wait Until Element Is Visible    ${CSS_KERNEL_IDLE}    timeout=${timeout}

Wait For JupyterLite
    Wait Until Page Contains Element    ${CSS_SPINNER}
    Wait Until Element Is Not Visible    ${CSS_SPINNER}    timeout=30s
    Wait Until Element Is Not Visible    ${CSS_SPLASH}    timeout=30s
    Wait Until Element Is Visible    ${CSS_LAUNCHER}

# capture #########################################################################################

Capture All Elements
    [Arguments]    ${stem}    ${selector}    ${ext}=png    ${tag}=${FALSE}
    ${els} =    Get WebElements    ${selector}
    IF    ${tag}    Set Tags    ${stem}:${els.__len__()}
    ${el_files} =    Create List
    FOR    ${i}    ${el}    IN ENUMERATE    @{els}
        ${i_just} =    Evaluate    "${i}".rjust(2, "0")
        VAR    ${screen} =    ${stem}-${i_just}-{index}.${ext}
        ${file} =    Capture Element Screenshot    ${el}    ${screen}
        Append To List    ${el_files}    ${file}
    END
    RETURN    ${el_files}

Log All Elements
    [Arguments]    ${selector}    ${prefix}=${EMPTY}    ${level}=${EMPTY}    ${console}=${FALSE}
    ${els} =    Get WebElements    ${selector}
    FOR    ${i}    ${el}    IN ENUMERATE    @{els}
        Log Element Text    ${el}    ${level}    ${console}    ${prefix} ${i}
    END

Log Element Text
    [Arguments]    ${el}    ${level}    ${console}=${FALSE}    ${prefix}=${EMPTY}
    ${el_text} =    Get Text    ${el}
    ${el_text} =    Indent    ${el_text}    \t
    Log    ${prefix}${el_text}    level=${level}    console=${console}

# browser ###########################################################################################

Serve JupyterLite
    Create Directory    ${LOGS}
    VAR    ${host} =    127.0.0.1
    ${port} =    Get Unused Port
    Start Process
    ...    python -m http.server -b ${host} ${port}
    ...    shell=${TRUE}
    ...    cwd=${LITE}
    ...    stdout=${LOGS}${/}lite.log.txt
    ...    stderr=STDOUT
    Set Suite Variable    $LITE_URL    http://${host}:${port}/    children=${TRUE}
    Set Screenshot Directory    ${SCREENS}

Open Firefox
    [Arguments]    ${stem}
    Create Directory    ${DOWNLOADS}
    ${ff_options} =    Get Firefox Options
    ...    ui.prefersReducedMotion=${1}
    ...    devtools.console.stdout.content=${True}
    ...    browser.download.folderList=${2}
    ...    browser.download.manager.showWhenStarting=${FALSE}
    ...    browser.download.dir=${DOWNLOADS}
    ...    browser.helperApps.neverAsk.saveToDisk=application/octet-stream,text/json,application/json,text/plain
    VAR    ${geckolog} =    ${LOGS}${/}geckodriver-${stem}.log.txt
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

Get Unused Port
    ${port} =    Evaluate
    ...    [s := socket.socket(), s.bind(("", 0)), s.getsockname()[1]][2]
    ...    modules=socket
    RETURN    ${port}
