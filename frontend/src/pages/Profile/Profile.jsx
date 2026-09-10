import "./Profile.css";
import Layout from "../../components/Layout/Layout";
import {
  PageHeader,
  StatusBadge,
  roleLabel,
} from "../../components/AdminUI/AdminUI";
import { getProfile } from "../../utils/storage";

function Profile() {
  const profile = getProfile();
  const unavailable = "Non disponible";

  return (
    <Layout>
      <main className="admin-page">
        <PageHeader
          title="Mon profil"
          description="Consultez vos informations professionnelles."
        />

        {profile ? (
          <div className="profile-page-grid">
            <section className="panel profile-summary">
              <div className="profile-hero">
                <div className="profile-photo">
                  {profile.first_name?.[0] || "?"}
                  {profile.last_name?.[0] || ""}
                </div>

                <div>
                  <h2>
                    {profile.first_name || unavailable}{" "}
                    {profile.last_name || ""}
                  </h2>

                  <p>{roleLabel(profile.role)}</p>
                </div>
              </div>

              <div className="profile-info">
                <div>
                  <span>Email</span>
                  <strong>{profile.email || unavailable}</strong>
                </div>

                <div>
                  <span>Téléphone</span>
                  <strong>{profile.phone || unavailable}</strong>
                </div>

                <div>
                  <span>Département</span>
                  <strong>{profile.department || unavailable}</strong>
                </div>

                <div>
                  <span>Rôle</span>
                  <strong>{roleLabel(profile.role)}</strong>
                </div>

                <div>
                  <span>Statut</span>
                  <StatusBadge value={profile.status} />
                </div>
              </div>
            </section>
          </div>
        ) : (
          <div className="panel">
            <p>Profil non disponible.</p>
          </div>
        )}
      </main>
    </Layout>
  );
}

export default Profile;