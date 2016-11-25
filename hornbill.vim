function GenEDT()
    let current_line = line('.')
    let current_filename = expand('%:p')
    let command = join(["~/Documents/independence_day/hornbill/hornbill.py edt", current_filename, current_line], " ")
    let @a = system(command)
    normal {"ap
endfunction

function GenDoxygen()
    let current_line = line('.')
    let current_filename = expand('%:p')
    let command = join(["~/Documents/independence_day/hornbill/hornbill.py doxygen", current_filename, current_line], " ")
    let @a = system(command)
    normal {"ap
endfunction
