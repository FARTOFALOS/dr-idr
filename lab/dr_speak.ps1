param(
    [Parameter(Mandatory=$true)][ValidateSet('NQ','ES','YM')][string]$Instrument,
    [ValidateSet('0.5','1')][string]$StandardDeviation,
    [switch]$TestAudio
)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Speech
$drSpeaker = New-Object System.Speech.Synthesis.SpeechSynthesizer
try {
    $drFemale = @($drSpeaker.GetInstalledVoices() | Where-Object {
        $_.Enabled -and $_.VoiceInfo.Gender -eq 'Female' -and $_.VoiceInfo.Culture.Name -eq 'en-US'
    } | Sort-Object { if ($_.VoiceInfo.Name -eq 'Microsoft Zira Desktop') { 0 } else { 1 } })
    if (-not $drFemale.Count) { throw 'No enabled English female voice installed' }
    $drSpeaker.SelectVoice($drFemale[0].VoiceInfo.Name)
    $drSpeaker.SetOutputToDefaultAudioDevice()
    $drSpeaker.Rate = 5
    $drSpeaker.Volume = 100
    $drLetters = ($Instrument.ToCharArray() | ForEach-Object { [string]$_ }) -join ' '
    $phrase = if ($StandardDeviation) {
        $level = if ($StandardDeviation -eq '0.5') { 'zero point five' } else { 'one' }
        "$drLetters, $level standard deviation. Tuk."
    } else {
        "Activation D R, $drLetters"
    }
    if ($TestAudio) { $phrase = "Audio test. $phrase" }
    $text = [Security.SecurityElement]::Escape($phrase)
    $drSpeaker.SpeakSsml("<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='en-US'><prosody pitch='+15%'>$text</prosody></speak>")
} finally { $drSpeaker.Dispose() }
