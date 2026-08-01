' ============================================================================
'  EUROSOFT Directory Protocol  —  handler "eurosoftdir://"
'  Otevře Windows Explorer na cestě předané z webové aplikace STRATEGIE.
'  Volá se z registru:  wscript.exe eurosoftdir_open.vbs "eurosoftdir://%5C%5C..."
'  Bez okna, bez flashe. Bezpečnostní pojistka: povolí jen datový server.
' ============================================================================
Option Explicit
Dim args, u, p, sh
Set args = WScript.Arguments
If args.Count = 0 Then WScript.Quit

u = args(0)

If InStr(1, u, "eurosoftdir:", vbTextCompare) = 1 Then
  u = Mid(u, Len("eurosoftdir:") + 1)
End If

Do While Len(u) > 0 And Left(u, 1) = "/"
  u = Mid(u, 2)
Loop

p = URLDecode(u)
p = Replace(p, "/", "\")

Dim allowed
allowed = False
If LCase(Left(p, 16)) = "\\192.168.30.11\" Then allowed = True
' If LCase(Left(p, 16)) = "\\192.168.30.21\" Then allowed = True   ' např. IT_Data

If allowed Then
  Set sh = CreateObject("WScript.Shell")
  sh.Run "explorer.exe """ & p & """", 1, False
End If

Function URLDecode(s)
  Dim i, c, res
  res = "" : i = 1
  Do While i <= Len(s)
    c = Mid(s, i, 1)
    If c = "%" And i + 2 <= Len(s) Then
      res = res & Chr(CLng("&H" & Mid(s, i + 1, 2)))
      i = i + 3
    ElseIf c = "+" Then
      res = res & " " : i = i + 1
    Else
      res = res & c : i = i + 1
    End If
  Loop
  URLDecode = res
End Function
