Get-ChildItem Cert:/LocalMachine/Root | Where-Object Subject -match test.nonexistant | Remove-Item
