document.addEventListener('DOMContentLoaded', function() {
    // Sidebar Toggle
    const sidebarToggle = document.getElementById('sidebarToggle');
    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', function(e) {
            e.preventDefault();
            document.body.classList.toggle('sb-sidenav-toggled');
        });
    }

    // Close sidebar on mobile when clicking outside
    document.addEventListener('click', function(e) {
        if (window.innerWidth < 992) {
            const sidebar = document.getElementById('sidebar-wrapper');
            const toggle = document.getElementById('sidebarToggle');
            if (sidebar && toggle && !sidebar.contains(e.target) && !toggle.contains(e.target)) {
                document.body.classList.remove('sb-sidenav-toggled');
            }
        }
    });
});
