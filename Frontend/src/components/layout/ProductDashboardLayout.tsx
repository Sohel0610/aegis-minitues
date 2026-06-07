import { ReactNode, useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import {
  ChevronLeft,
  ChevronRight,
  Menu,
  LucideIcon,
  X,
} from "lucide-react";
import UserManualModal from "../UserManualModal";

// Adani theme color constants — same as outside design
const A = {
  navy: "#FFFFFF",
  navyMid: "#F8FAFB",
  orange: "#0066B3",
  orangeLight: "#0080D6",
  blue: "#0057B8",
  text: "#323232",
  muted: "#64748B",
  border: "rgba(0,0,0,0.08)",
};

interface ProductDashboardLayoutProps {
  children: ReactNode;
  productName: string;
  productRoute: string;
  navigationItems: NavigationItem[];
}

interface NavigationItem {
  id: string;
  label: string;
  icon: LucideIcon;
  href: string;
  isActive?: boolean;
}

const ProductDashboardLayout = ({
  children,
  productName,
  productRoute,
  navigationItems,
}: ProductDashboardLayoutProps) => {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [isMobileOpen, setIsMobileOpen] = useState(false);
  const [isUserManualOpen, setIsUserManualOpen] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  const handleNavigation = (item: NavigationItem): void => {
    if (item.id === "manual") {
      setIsUserManualOpen(true);
      if (isMobileOpen) setIsMobileOpen(false);
      return;
    }
    navigate(item.href);
    if (isMobileOpen) setIsMobileOpen(false);
  };

  const sidebarWidth = isCollapsed ? 68 : 238;

  // Separate main nav items and resource items
  const mainNavItems = navigationItems.filter(
    (item) =>
      !["documentation", "user-guide", "servicenow-guide"].includes(item.id)
  );
  const resourceItems = navigationItems.filter((item) =>
    ["documentation", "user-guide", "servicenow-guide"].includes(item.id)
  );

  const renderNavButton = (item: NavigationItem, collapsed: boolean) => {
    const IconComponent = item.icon;
    const active = item.isActive || false;
    return (
      <button
        key={item.id}
        onClick={() => handleNavigation(item)}
        title={collapsed ? item.label : undefined}
        style={{
          display: "flex",
          alignItems: "center",
          gap: 10,
          padding: collapsed ? "6px 0" : "7px 12px",
          borderRadius: 9,
          border: "none",
          cursor: "pointer",
          width: "100%",
          justifyContent: collapsed ? "center" : "flex-start",
          background: active ? "rgba(0,102,179,0.08)" : "transparent",
          transition: "all 0.15s ease",
          position: "relative",
          fontFamily: "'Adani', sans-serif",
        }}
      >
        <IconComponent
          size={17}
          color={active ? A.orange : A.muted}
          strokeWidth={active ? 2.5 : 2}
          style={{ flexShrink: 0 }}
        />
        {!collapsed && (
          <span
            style={{
              fontSize: 13.5,
              color: active ? A.text : A.muted,
              fontWeight: active ? 600 : 400,
            }}
          >
            {item.label}
          </span>
        )}
        {active && !collapsed && (
          <div
            style={{
              position: "absolute",
              right: 10,
              width: 6,
              height: 6,
              borderRadius: "50%",
              background: A.orange,
            }}
          />
        )}
      </button>
    );
  };

  return (
    <div
      style={{
        display: "flex",
        height: "100vh",
        overflow: "hidden",
        fontFamily: "'Adani', -apple-system, BlinkMacSystemFont, sans-serif",
        background: "#F8FAFB",
        color: "#323232",
      }}
    >
      {/* Mobile Menu Button */}
      <button
        onClick={() => setIsMobileOpen(!isMobileOpen)}
        style={{
          display: "none",
          position: "fixed",
          top: 16,
          left: 16,
          zIndex: 50,
          padding: 8,
          borderRadius: 8,
          background: "rgba(0,102,179,0.1)",
          border: `1px solid ${A.border}`,
          cursor: "pointer",
          color: A.orange,
        }}
        className="mobile-menu-btn"
      >
        <Menu size={20} />
      </button>

      {/* Desktop Sidebar */}
      <aside
        style={{
          width: sidebarWidth,
          minWidth: sidebarWidth,
          transition:
            "width 0.25s cubic-bezier(.4,0,.2,1), min-width 0.25s cubic-bezier(.4,0,.2,1)",
          background: "#FFFFFF",
          borderRight: `1px solid ${A.border}`,
          display: "flex",
          flexDirection: "column",
          position: "relative",
          boxShadow: "2px 0 8px rgba(0,0,0,0.04)",
          overflow: "hidden",
        }}
      >
        {/* Blue accent top bar */}
        <div
          style={{
            height: 3,
            background: `linear-gradient(90deg, ${A.orange}, ${A.orangeLight}, transparent)`,
            flexShrink: 0,
          }}
        />

        {/* Logo */}
        <div
          style={{
            padding: isCollapsed ? "12px 0" : "12px 16px",
            display: "flex",
            alignItems: "center",
            gap: 10,
            justifyContent: isCollapsed ? "center" : "flex-start",
            borderBottom: `1px solid ${A.border}`,
            minHeight: 56,
            flexShrink: 0,
          }}
        >
          <img
            src="/adani.svg"
            alt="Adani"
            style={{
              height: isCollapsed ? 28 : 32,
              width: "auto",
              flexShrink: 0,
            }}
          />
          {!isCollapsed && (
            <div style={{ overflow: "hidden" }}>
              <div
                style={{
                  fontSize: 14,
                  color: A.text,
                  fontWeight: 700,
                  marginTop: 2,
                }}
              >
                {productName}
              </div>

            </div>
          )}
        </div>

        {/* Main nav */}
        <nav
          style={{
            flex: 1,
            minHeight: 0,
            padding: "8px 8px",
            display: "flex",
            flexDirection: "column",
            gap: 2,
            overflowY: "auto",
            scrollbarWidth: "none",
            msOverflowStyle: "none",
          }}
        >
          {!isCollapsed && (
            <div
              style={{
                fontSize: 9.5,
                color: A.muted,
                textTransform: "uppercase",
                letterSpacing: "0.1em",
                fontWeight: 700,
                padding: "4px 10px 8px",
              }}
            >
              Main Menu
            </div>
          )}
          {mainNavItems.map((item) => renderNavButton(item, isCollapsed))}

          <div style={{ flex: 1 }} />

          {resourceItems.length > 0 && (
            <>
              {!isCollapsed && (
                <div
                  style={{
                    fontSize: 9.5,
                    color: A.muted,
                    textTransform: "uppercase",
                    letterSpacing: "0.1em",
                    fontWeight: 700,
                    padding: "8px 10px 6px",
                  }}
                >
                  Resources
                </div>
              )}
              {resourceItems.map((item) => renderNavButton(item, isCollapsed))}
            </>
          )}
        </nav>

        <div
          style={{
            padding: "12px 12px",
            display: "flex",
            justifyContent: "flex-end",
            borderTop: isCollapsed ? "none" : `1px solid ${A.border}`,
            flexShrink: 0,
          }}
        >
          <button
            onClick={() => setIsCollapsed(!isCollapsed)}
            style={{
              width: 32,
              height: 32,
              borderRadius: 8,
              background: "rgba(0,102,179,0.05)",
              border: `1px solid ${A.border}`,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              cursor: "pointer",
              color: A.orange,
              transition: "all 0.2s ease",
            }}
          >
            {isCollapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
          </button>
        </div>
      </aside>

      {/* Mobile Sidebar Overlay */}
      {isMobileOpen && (
        <div
          style={{
            position: "fixed",
            inset: 0,
            zIndex: 100,
            background: "rgba(0,0,0,0.5)",
          }}
          onClick={() => setIsMobileOpen(false)}
        >
          <aside
            style={{
              width: 260,
              height: "100%",
              background: "#FFFFFF",
              borderRight: `1px solid ${A.border}`,
              display: "flex",
              flexDirection: "column",
              boxShadow: "2px 0 12px rgba(0,0,0,0.1)",
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div
              style={{
                height: 3,
                background: `linear-gradient(90deg, ${A.orange}, ${A.orangeLight}, transparent)`,
                flexShrink: 0,
              }}
            />
            <div
              style={{
                padding: "18px 20px",
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                borderBottom: `1px solid ${A.border}`,
                minHeight: 70,
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                <img
                  src="/adani.svg"
                  alt="Adani"
                  style={{ height: 32, width: "auto" }}
                />
                <div>
                  <div
                    style={{
                      fontSize: 14,
                      color: A.text,
                      fontWeight: 700,
                    }}
                  >
                    {productName}
                  </div>

                </div>
              </div>
              <button
                onClick={() => setIsMobileOpen(false)}
                style={{
                  background: "none",
                  border: "none",
                  cursor: "pointer",
                  color: A.muted,
                }}
              >
                <X size={18} />
              </button>
            </div>
            <nav
              style={{
                flex: 1,
                padding: "14px 8px",
                display: "flex",
                flexDirection: "column",
                gap: 2,
                overflowY: "auto",
              }}
            >
              <div
                style={{
                  fontSize: 9.5,
                  color: A.muted,
                  textTransform: "uppercase",
                  letterSpacing: "0.1em",
                  fontWeight: 700,
                  padding: "4px 10px 8px",
                }}
              >
                Main Menu
              </div>
              {mainNavItems.map((item) => renderNavButton(item, false))}
              <div style={{ flex: 1 }} />
              {resourceItems.length > 0 && (
                <>
                  <div
                    style={{
                      fontSize: 9.5,
                      color: A.muted,
                      textTransform: "uppercase",
                      letterSpacing: "0.1em",
                      fontWeight: 700,
                      padding: "8px 10px 6px",
                    }}
                  >
                    Resources
                  </div>
                  {resourceItems.map((item) => renderNavButton(item, false))}
                </>
              )}
            </nav>
          </aside>
        </div>
      )}

      {/* Main Content */}
      <main
        style={{
          flex: 1,
          minWidth: 0,
          overflowY: "auto",
          overflowX: "hidden",
        }}
      >
        {children}
      </main>

      {/* User Manual Modal */}
      <UserManualModal
        isOpen={isUserManualOpen}
        onClose={() => setIsUserManualOpen(false)}
        initialAgent={
          productName === "Generate Minutes"
            ? "Generate Minutes Agent"
            : undefined
        }
      />
    </div>
  );
};

export default ProductDashboardLayout;