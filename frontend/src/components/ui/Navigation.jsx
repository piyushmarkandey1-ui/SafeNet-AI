/**
 * SafeNet AI — Global Navigation
 * Powered by PillNav from React Bits, styled to the SafeNet color scheme.
 */
import { useLocation } from 'react-router-dom';
import PillNav from './PillNav';

const NAV_ITEMS = [
  { label: 'Home',           href: '/' },
  { label: 'Dashboard',      href: '/dashboard' },
  { label: 'Note Checker',   href: '/note-checker' },
  { label: 'Number Checker', href: '/number-checker' },
];

export function Navigation() {
  const location = useLocation();

  // Determine active href (exact for home, prefix for rest)
  const activeHref = NAV_ITEMS.slice().reverse().find(item =>
    item.href === '/'
      ? location.pathname === '/'
      : location.pathname.startsWith(item.href)
  )?.href;

  return (
    <PillNav
      logo="/favicon.svg"
      logoAlt="SafeNet AI"
      items={NAV_ITEMS}
      activeHref={activeHref}
      initialLoadAnimation={true}
      ease="power3.out"
      /* SafeNet color palette */
      baseColor="#2ec4b6"          /* teal — used for hover-circle fill & hover text bg */
      pillColor="#1A2332"           /* bg-elevated — each pill background */
      pillTextColor="#F0F2F5"       /* text-primary */
      hoveredPillTextColor="#0A0E14" /* dark text on teal hover circle */
    />
  );
}
