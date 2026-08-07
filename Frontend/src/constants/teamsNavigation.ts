/**
 * Shared navigation items for the MS Teams Meetings module.
 * Single source of truth — imported by all Teams sub-pages.
 */
import {
  Home,
  Video,
  FileText,
  Brain,
  BarChart3,
  BookOpen,
  LucideIcon
} from 'lucide-react';

export interface TeamsNavItem {
  id: string;
  label: string;
  icon: LucideIcon;
  href: string;
  isActive?: boolean;
}

/**
 * Returns navigation items for the Teams Meetings module sidebar.
 */
export function getTeamsNavItems(activeId?: string): TeamsNavItem[] {
  const items: TeamsNavItem[] = [
    { id: 'home', label: 'Home', icon: Home, href: '/' },
    { id: 'meetings', label: 'Meetings', icon: Video, href: '/teams-meetings' },
    { id: 'manual', label: 'User Manual', icon: BookOpen, href: '#' },
  ];

  if (activeId) {
    return items.map(item => ({
      ...item,
      isActive: item.id === activeId,
    }));
  }

  return items;
}
