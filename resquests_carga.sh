while ($true) {
    # Sorteia um número de 0 a 3 para escolher o cenário de teste
    $sorteio = Get-Random -Min 0 -Max 4
    
    switch ($sorteio) {
        0 { $rota = "rolldice?player=Maria" }
        1 { $rota = "rolldice?player=Joao" }
        2 { $rota = "rolldice" }               # Jogador Anônimo
        3 { $rota = "sim-workflow" }           # Rota de erro/workflow
    }
    
    # Executa a requisição HTTP usando o curl nativo do Windows
    $resultado = curl.exe -s "http://localhost:8000/$rota"
    
    # Printa na tela o que foi chamado para você acompanhar o tráfego
    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Efetuado: /$rota" -ForegroundColor Cyan
    
    # Aguarda 1 segundo antes de disparar o próximo para não travar a máquina
    Start-Sleep -Seconds 1
}
