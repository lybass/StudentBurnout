// StudentBurnout - script principal (comportements légers côté client)
document.addEventListener('DOMContentLoaded', function () {
  // Fermeture automatique des alertes après quelques secondes
  document.querySelectorAll('.alert-dismissible').forEach(function (alertEl) {
    setTimeout(function () {
      const alert = bootstrap.Alert.getOrCreateInstance(alertEl);
      if (alert) {
        alert.close();
      }
    }, 6000);
  });
});
