param([Parameter(Mandatory=$true)][string]$Source,[Parameter(Mandatory=$true)][string]$Target)
$ErrorActionPreference='Stop'
if(-not ('KStudioBundleVerifier' -as [type])){
Add-Type -TypeDefinition @'
using System;
using System.IO;
using System.Security.Cryptography;
using System.Collections.Concurrent;
using System.Threading.Tasks;
public static class KStudioBundleVerifier {
  public static string[] Verify(string source, string target, string[] files) {
    var failures = new ConcurrentBag<string>();
    Parallel.ForEach(files, new ParallelOptions { MaxDegreeOfParallelism = 8 }, file => {
      string relative = file.Substring(source.Length).TrimStart('\\', '/');
      try {
        byte[] left, right;
        using(var sha = SHA256.Create()) {
          using(var stream = File.OpenRead(file)) left = sha.ComputeHash(stream);
          using(var stream = File.OpenRead(Path.Combine(target, relative))) right = sha.ComputeHash(stream);
        }
        if(!BitConverter.ToString(left).Equals(BitConverter.ToString(right))) failures.Add(relative);
      } catch(Exception) { failures.Add(relative + ": unable to verify both files"); }
    });
    return failures.ToArray();
  }
}
'@
}
$sourcePath=[IO.Path]::GetFullPath($Source).TrimEnd('\','/')
$targetPath=[IO.Path]::GetFullPath($Target).TrimEnd('\','/')
$files=[IO.Directory]::GetFiles($sourcePath,'*',[IO.SearchOption]::AllDirectories)
if(-not $files.Length){throw '源程序包为空。'}
$failures=[KStudioBundleVerifier]::Verify($sourcePath,$targetPath,$files)
if($failures.Length){throw ('安装文件校验失败：'+($failures -join ', '))}
Write-Output $files.Length
