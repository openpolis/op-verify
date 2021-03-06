# -*- coding: utf-8 -*-
from django.db import models
from django.db import connections
from django.conf import settings
from django.db.models.query import QuerySet
from django.utils.encoding import smart_unicode

# edit to load from other database
DBNAME = 'politici'


def dict_fetchall(cursor):
    """Returns all rows from a cursor as a dict"""
    desc = cursor.description
    return [
        dict(zip([col[0] for col in desc], row))
        for row in cursor.fetchall()
    ]


class OpUser(models.Model):
    id = models.IntegerField(primary_key=True)
    location = models.ForeignKey('OpLocation', null=True, blank=True)
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    nickname = models.CharField(max_length=16, blank=True)
    is_active = models.IntegerField()
    email = models.CharField(max_length=100)
    sha1_password = models.CharField(unique=True, max_length=40, blank=True)
    salt = models.CharField(max_length=32, blank=True)
    want_to_be_moderator = models.IntegerField(null=True, blank=True)
    is_moderator = models.IntegerField(null=True, blank=True)
    is_administrator = models.IntegerField(null=True, blank=True)
    deletions = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True)
    picture = models.TextField(blank=True)
    url_personal_website = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)
    has_paypal = models.IntegerField(null=True, blank=True)
    remember_key = models.CharField(max_length=64, blank=True)
    wants_newsletter = models.IntegerField()
    public_name = models.IntegerField()
    charges = models.IntegerField(null=True, blank=True)
    resources = models.IntegerField(null=True, blank=True)
    declarations = models.IntegerField(null=True, blank=True)
    themes = models.IntegerField(null=True, blank=True)
    comments = models.IntegerField(null=True, blank=True)
    last_contribution = models.DateTimeField(null=True, blank=True)
    is_premium = models.IntegerField(null=True, blank=True)
    is_adhoc = models.IntegerField(null=True, blank=True)
    is_aggiungitor = models.IntegerField(null=True, blank=True)
    class Meta:
        db_table = u'op_user'
        managed = False




class OpContent(models.Model):
    id = models.IntegerField(primary_key=True)
    reports = models.IntegerField()
    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)
    op_table = models.CharField(max_length=128, blank=True)
    op_class = models.CharField(max_length=128, blank=True)
    hash = models.CharField(max_length=32, blank=True)
    class Meta:
        db_table = u'op_content'
        managed = False


class OpOpenContent(models.Model):
    content = models.OneToOneField('OpContent', primary_key=True, db_column='content_id')
    user = models.ForeignKey('OpUser')
    deleted_at = models.DateTimeField(null=True, blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    class Meta:
        db_table = u'op_open_content'
        managed = False


class OpProfessionManager(models.Manager):
    def getBasic(self):
        return self.filter(oid__isnull=True)



class OpProfession(models.Model):
    id = models.IntegerField(primary_key=True)
    description = models.CharField(max_length=255)
    oid = models.IntegerField(null=True, blank=True)
    odescription = models.CharField(max_length=255, blank=True)
    objects = OpProfessionManager()

    class Meta:
        db_table = u'op_profession'
        managed = False

    def getNormalizedDescription(self):
        if self.oid is not None:
            norm = OpProfession.objects.db_manager('politici').get(pk=self.oid)
            return norm.description
        else:
            return self.description

    def __unicode__(self):
        return self.getNormalizedDescription()


class OpElectionType(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=32)
    class Meta:
        db_table = u'op_election_type'
        managed = False


class OpElection(models.Model):
    id = models.IntegerField(primary_key=True)
    election_date = models.DateField(unique=True, null=True, blank=True)
    election_type = models.ForeignKey('OpElectionType')
    location = models.ForeignKey('OpLocation')
    class Meta:
        db_table = u'op_election'
        managed = False


class OpPolitician(models.Model):
    content = models.OneToOneField('OpContent', primary_key=True, db_column='content_id')
    profession = models.ForeignKey('OpProfession', null=True, blank=True)
    user = models.ForeignKey(OpUser, null=True, blank=True, related_name='oppolitician_user_set')
    first_name = models.CharField(max_length=64, blank=True)
    last_name = models.CharField(max_length=64, blank=True)
    sex = models.CharField(max_length=1, blank=True)
    picture = models.TextField(blank=True)
    birth_date = models.DateTimeField(null=True, blank=True)
    birth_location = models.CharField(max_length=128, blank=True)
    death_date = models.DateTimeField(null=True, blank=True)
    last_charge_update = models.DateTimeField(null=True, blank=True)
    is_indexed = models.IntegerField()
    minint_aka = models.CharField(unique=True, max_length=255, blank=True)
    creator = models.ForeignKey('OpUser', null=True, blank=True, related_name='oppolitician_creator_set')

    class Meta:
        db_table = u'op_politician'
        managed = False


    def getInstitutionCharges(self, type=None):
        """docstring for getInstitutionCharges"""
        if type == 'current':
            pol_charges = self.opinstitutioncharge_set.db_manager('politici').filter(
                date_end__isnull=True,
                content__deleted_at__isnull=True,
                ).order_by('-date_start')
        elif type == 'past':
            pol_charges = self.opinstitutioncharge_set.db_manager('politici').filter(
                date_end__isnull=False,
                content__deleted_at__isnull=True,
                ).order_by('-date_end')
        else:
            pol_charges = self.opinstitutioncharge_set.db_manager('politici').filter(
                content__deleted_at__isnull=True,
                )
        charges = []
        for charge in pol_charges:
            charges.append({
                'date_start': charge.date_start,
                'date_end': charge.date_end,
                'description': charge.description,
                'institution': charge.institution.name,
                'charge_type': charge.charge_type.name,
                'location': charge.location.name,
                'location_id': charge.location.id,
                'group': charge.group.name,
                'party': charge.party.name,
                'textual_rep': charge.getTextualRepresentation(),
                })
        return charges


    def getPoliticalCharges(self, type=None):
        """get current or past political charges"""
        if type == 'current':
            pol_charges = self.oppoliticalcharge_set.db_manager('politici').filter(
                date_end__isnull=True,
                content__deleted_at__isnull=True,
                ).order_by('-date_start')
        elif type == 'past':
            pol_charges = self.oppoliticalcharge_set.db_manager('politici').filter(
                date_end__isnull=False,
                content__deleted_at__isnull=True,
                ).order_by('-date_end')
        else:
            pol_charges = self.oppoliticalcharge_set.db_manager('politici').filter(
                content__deleted_at__isnull=True,
                ).order_by('-date_end')
        charges = []
        for charge in pol_charges:
            charges.append({
                'date_start': charge.date_start,
                'date_end': charge.date_end,
                'description': charge.description,
                'charge_type': charge.charge_type.name,
                'location': charge.location.name,
                'location_id': charge.location.id,
                'party': charge.party.name,
                'textual_rep': charge.getTextualRepresentation(),
                })
        return charges


    def getOrganizationCharges(self, type=None):
        """get current or past political charges"""
        if type == 'current':
            pol_charges = self.oporganizationcharge_set.db_manager('politici').filter(
                date_end__isnull=True,
                content__deleted_at__isnull=True,
                ).order_by('-date_start')
        elif type == 'past':
            pol_charges = self.oporganizationcharge_set.db_manager('politici').filter(
                date_end__isnull=False,
                content__deleted_at__isnull=True,
                ).order_by('-date_end')
        else:
            pol_charges = self.oporganizationcharge_set.db_manager('politici').filter(
                content__deleted_at__isnull=True,
                ).order_by('-date_end')
        charges = []
        for charge in pol_charges:
            charges.append({
                'date_start': charge.date_start,
                'date_end': charge.date_end,
                'charge_name': charge.charge_name.encode('utf8'),
                'organization': charge.organization.name,
                'textual_rep': charge.getTextualRepresentation(),
                })

        return charges

    def get_image_uri(self):
        return "http://politici.openpolis.it/politician/picture?content_id={}".format(self.content_id)

    @property
    def resources(self):
        return self.opresources_set.filter(content__deleted_at__isnull=True)

    @property
    def education_levels(self):
        return self.oppoliticianhasopeducationlevel_set.all()

    @property
    def institution_charges(self):
        return self.opinstitutioncharge_set.filter(content__deleted_at__isnull=True)

    @property
    def political_charges(self):
        return self.oppoliticalcharge_set.filter(content__deleted_at__isnull=True)

    @property
    def organization_charges(self):
        return self.oporganizationcharge_set.filter(content__deleted_at__isnull=True)
#        return u"{} {}".format(self.first_name, self.last_name).title()



class OpEducationLevelManager(models.Manager):
    def getBasic(self):
        return self.filter(oid__isnull=True)


class OpEducationLevel(models.Model):
    id = models.IntegerField(primary_key=True)
    description = models.CharField(max_length=255)
    oid = models.IntegerField(null=True, blank=True)
    odescription = models.CharField(max_length=255, blank=True)
    objects = OpEducationLevelManager()

    class Meta:
        db_table = u'op_education_level'
        managed = False

    def __unicode__(self):
        return self.getNormalizedDescription()

    def getNormalizedDescription(self):
        if self.oid is not None:
            norm = OpEducationLevel.objects.db_manager('politici').get(pk=self.oid)
            return norm.description
        else:
            return self.description


class OpPoliticianHasOpEducationLevel(models.Model):
    politician = models.ForeignKey('OpPolitician', primary_key=True)
    education_level = models.ForeignKey('OpEducationLevel', primary_key=True)
    description = models.CharField(max_length=255, blank=True)

    def __unicode__(self):
        if self.description:
            return u"{0} ({1})".format(self.education_level, self.description)
        else:
            return u"{0}".format(self.education_level)

    class Meta:
        db_table = u'op_politician_has_op_education_level'
        managed = False



class OpInstitution(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=255, blank=True)
    short_name = models.CharField(max_length=45, blank=True)
    priority = models.IntegerField(null=True, blank=True)

    def __unicode__(self):
        return self.name

    class Meta:
        db_table = u'op_institution'
        managed = False



class OpChargeType(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=255, blank=True)
    short_name = models.CharField(max_length=45, blank=True)
    priority = models.IntegerField(null=True, blank=True)
    category = models.CharField(max_length=1)

    def __unicode__(self):
        return self.name

    class Meta:
        db_table = u'op_charge_type'
        managed = False


class OpInstitutionHasChargeType(models.Model):
    institution = models.ForeignKey('OpInstitution')
    charge_type = models.ForeignKey('OpChargeType')
    class Meta:
        db_table = u'op_institution_has_charge_type'
        managed = False


class OpConstituency(models.Model):
    id = models.IntegerField(primary_key=True)
    election_type = models.ForeignKey('OpElectionType')
    name = models.CharField(max_length=255, blank=True)
    slug = models.CharField(max_length=128, blank=True)
    valid = models.IntegerField(null=True, blank=True)
    class Meta:
        db_table = u'op_constituency'
        managed = False


class OpConstituencyLocation(models.Model):
    constituency = models.ForeignKey('OpConstituency')
    location = models.ForeignKey('OpLocation')
    class Meta:
        db_table = u'op_constituency_location'
        managed = False


class OpParty(models.Model):
    id = models.IntegerField(primary_key=True)
    istat_code = models.CharField(max_length=15, blank=True)
    name = models.CharField(unique=True, max_length=80)
    acronym = models.CharField(max_length=20, blank=True)
    party = models.IntegerField(null=True, blank=True)
    main = models.IntegerField(null=True, blank=True)
    electoral = models.IntegerField(null=True, blank=True)
    oid = models.IntegerField(null=True, blank=True)
    oname = models.CharField(max_length=80, blank=True)
    logo = models.TextField(blank=True)

    class Meta:
        db_table = u'op_party'
        managed = False

    def getNormalized(self):
        """look up for normalized partied in the db"""
        if self.oid is not None and self.oid != 0:
            return OpParty.objects.db_manager('politici').get(pk=self.oid)
        else:
            return self


    def getName(self):
        """get original, hand-modified name, if present"""
        if self.oname:
            return self.oname
        else:
            return self.name


    def hasAcronym(self):
        """check for acronym existance"""
        return self.acronym is not None and self.acronym.strip() != ''


    def getAcronymOrName(self):
        """return acronym if it exists, else, the name"""
        if self.hasAcronym():
            return self.acronym
        else:
            return self.getName()


    def getNormalizedAcronymOrName(self):
        """lookup the normalized party, then return the acronym or the name"""
        norm = self.getNormalized()
        return norm.getAcronymOrName()



class OpPartyLocation(models.Model):
    party = models.ForeignKey('OpParty')
    location = models.ForeignKey('OpLocation')
    class Meta:
        db_table = u'op_party_location'
        managed = False


class OpGroup(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(unique=True, max_length=255, blank=True)
    acronym = models.CharField(max_length=80, blank=True)
    oid = models.IntegerField(null=True, blank=True)
    oname = models.CharField(max_length=80, blank=True)

    class Meta:
        db_table = u'op_group'
        managed = False

    def getNormalized(self):
        """look up for normalized group in the db"""
        if self.oid is not None and self.oid != 0:
            return OpGroup.objects.db_manager('politici').get(pk=self.oid)
        else:
            return self


    def getName(self):
        """get original, hand-modified name, if present"""
        if self.oname:
            return self.oname
        else:
            return self.name


    def hasAcronym(self):
        """check for acronym existance"""
        return self.acronym is not None and self.acronym.strip() != ''


    def getAcronymOrName(self):
        """return acronym if it exists, else, the name"""
        if self.hasAcronym():
            return self.acronym
        else:
            return self.getName()


    def getNormalizedAcronymOrName(self):
        """lookup the normalized party, then return the acronym or the name"""
        norm = self.getNormalized()
        return norm.getAcronymOrName()




class OpGroupLocation(models.Model):
    group = models.ForeignKey('OpGroup')
    location = models.ForeignKey('OpLocation')
    class Meta:
        db_table = u'op_group_location'
        managed = False


class OpInstitutionChargeManager(models.Manager):
    """class to handle queries on OpInstitutionCharge"""

    def get_statistics(self, request):
        cursor = connections['politici'].cursor()

        base_sql = """
            from op_institution_charge ic, op_institution i, op_open_content oc, op_politician p, 
              op_location l, op_profession pr, op_politician_has_op_education_level pe, op_education_level e 
            where l.id=ic.location_id and ic.institution_id=i.id and 
              ic.politician_id=p.content_id and oc.content_id=ic.content_id and
              p.profession_id=pr.id and p.content_id=pe.politician_id and
              pe.education_level_id=e.id and  
              oc.deleted_at is null and ic.date_end is null 
            """
        filters = {}
        results = {}

        clauses_sql = ""
        clauses_params = []


        #
        # building filters
        #

        location_types = ('all', 'regional', 'provincial', 'city')
        location_id = 0
        if 'location_id' in request.GET:
            location_id = request.GET['location_id']
        location_type = 0
        if 'location_type' in request.GET:
            location_type = request.GET['location_type']
        if location_id != 0:
            if location_type in location_types:
                location = OpLocation.objects.db_manager('politici').getFromTypeId(location_type, location_id)
                clauses_sql += " and l.%s_id=%%s " % location_type
                clauses_params.append(location_id)
                filters['location_context'] = { 'type': location_type, 'id': location_id, 'name': location.name, 'op_location_id': location.id }
            else:
                raise Exception('wrong location type parameter: %s not in (regional, provincial, city)' % location_type)
        elif location_type == 'all':
            clauses_sql += " and l.location_type_id in (4, 5, 6) "
            filters['location_context'] = { 'type': 'all' }

        ages = {
            'twenties': 20,
            'thirties': 30,
            'forties': 40,
            'fifties': 50,
            'sixties': 60,
            'seventies': 70,
            'eighties': 80,
            'nineties': 90,
            'venerables': 100
        }
        age = 0
        if 'age' in request.GET:
            age = request.GET['age']
        if age != 0:
            if age in ages.keys():
                tenth = ages[age] / 10
                clauses_sql += " and YEAR(CURDATE())-YEAR(p.birth_date) < %d5 and YEAR(CURDATE())-YEAR(p.birth_date) >= %d5 " % (tenth, tenth-1)
                filters['age'] = age
            else:
                raise Exception('wrong age parameter: %s not in (twenties, thirties, ..., nineties, venerables)' % age)

        sexes = ('M', 'F')
        sex = 0
        if 'sex' in request.GET:
            sex = request.GET['sex']
        if sex != 0:
            if sex in sexes:
                clauses_sql += " and sex = %s"
                clauses_params.append(sex)
                filters['sex'] = sex
            else:
                raise Exception('wrong sex parameter: %s not in (M, F)' % sex)

        institutions = ('giunta_regionale', 'consiglio_regionale', 'giunta_provinciale', 'consiglio_provinciale', 'giunta_comunale', 'consiglio_comunale', 'commissariamento')
        institution = 0
        if 'institution' in request.GET:
            institution = request.GET['institution']
        if institution != 0:
            if institution in institutions:
                clauses_sql += " and i.name = %s"
                clauses_params.append(institution.replace('_', ' '))
                filters['institution'] = institution.replace('_', ' ')
            else:
                raise Exception('wrong institution parameter: %s not in (giunta_regionale, consiglio_regionale, ...)' % institution)

        professions = {}
        for profession in OpProfession.objects.db_manager('politici').getBasic().values('id', 'description', 'odescription'):
            if profession['odescription']:
                professions[profession['id']] = profession['odescription']
            else:
                professions[profession['id']] = profession['description']
        profession_id = 0
        if 'profession_id' in request.GET:
            profession_id = int(request.GET['profession_id'])
        if profession_id != 0:
            if profession_id in professions.keys():
                clauses_sql += " and (pr.id = %s or pr.oid = %s)"
                clauses_params.extend([profession_id, profession_id])
                filters['profession'] = { 'id': profession_id, 'name': professions[profession_id] }
            else:
                raise Exception('wrong institution parameter: %s not in professions_ids' % profession_id)

        educations = {}
        for education in OpEducationLevel.objects.db_manager('politici').getBasic().values('id', 'description'):
            educations[education['id']] = education['description']
        education_id = 0
        if 'education_id' in request.GET:
            education_id = int(request.GET['education_id'])
        if education_id != 0:
            if education_id in educations.keys():
                clauses_sql += " and (e.id = %s or e.oid = %s)"
                clauses_params.extend([education_id, education_id])
                filters['education'] = { 'id': education_id, 'name': educations[education_id] }
            else:
                raise Exception('wrong institution parameter: %s not in educations_ids' % education_id)

        #
        # building results
        #
        total_sql = "select count(*) as n %s %s" % (base_sql, clauses_sql)
        cursor.execute(total_sql, clauses_params)
        row = cursor.fetchone()
        results['total'] = row[0]

        age_numbers = {
            'twenties':   { 'count': 0 },
            'thirties':   { 'count': 0 },
            'fourties':   { 'count': 0 },
            'fifties':    { 'count': 0 },
            'sixties':    { 'count': 0 },
            'seventies':  { 'count': 0 },
            'eighties':   { 'count': 0 },
            'nineties':   { 'count': 0 },
            'venerables': { 'count': 0 }
        }
        if age == 0:
            age_sql = """select YEAR(CURDATE())-YEAR(p.birth_date) as age, count(*) as n
              %s %s      
              group by age order by n desc""" % (base_sql, clauses_sql)
            cursor.execute(age_sql, clauses_params)

            for row in cursor.fetchall():
                age = row[0]
                if age < 25:
                    age_numbers['twenties']['count'] += row[1]
                elif age >= 25 and age < 35:
                    age_numbers['thirties']['count'] += row[1]
                elif age >= 35 and age < 45:
                    age_numbers['fourties']['count'] += row[1]
                elif age >= 45 and age < 55:
                    age_numbers['fifties']['count'] += row[1]
                elif age >= 55 and age < 65:
                    age_numbers['sixties']['count'] += row[1]
                elif age >= 65 and age < 75:
                    age_numbers['seventies']['count'] += row[1]
                elif age >= 75 and age < 85:
                    age_numbers['eighties']['count'] += row[1]
                elif age >= 85 and age < 95:
                    age_numbers['nineties']['count'] += row[1]
                elif age >= 9:
                    age_numbers['venerables']['count'] += row[1]

            results['age'] = age_numbers


        if sex == 0:
            sex_sql = """select p.sex, count(*) as n
              %s %s      
              group by p.sex order by n desc""" % (base_sql, clauses_sql)
            cursor.execute(sex_sql, clauses_params)
            sex_numbers = {}
            for row in cursor.fetchall():
                sex = row[0]
                sex_numbers[sex] = int(row[1])

            if 'M' in sex_numbers.keys():
                sex_numbers_m = sex_numbers['M']
            else:
                sex_numbers_m = 0

            if 'F' in sex_numbers.keys():
                sex_numbers_f = sex_numbers['F']
            else:
                sex_numbers_f = 0

            results['sex'] = { 'M': { 'count': sex_numbers_m }, 'F': { 'count': sex_numbers_f } }


        institution_numbers = {}
        for inst in OpInstitution.objects.using('politici').all().values('id', 'name'):
            if 'giunta' in inst['name'].lower() or 'consiglio' in inst['name'].lower() or 'commissariamento' in inst['name'].lower():
                institution_numbers[inst['id']] = { 'name': inst['name'], 'count': 0 }
        if institution == 0:
            institution_sql = """select i.id, count(*) as n
              %s %s      
              group by i.id order by n desc""" % (base_sql, clauses_sql)
            cursor.execute(institution_sql, clauses_params)
            for row in cursor.fetchall():
                i_id = row[0]
                i_count = int(row[1])

                if i_id in institution_numbers:
                    institution_numbers[i_id]['count'] += i_count
                else:
                    if settings.DEBUG:
                        print "Impossibile trovare institution_id: %s" % (i_id,)

            results['institutions'] = institution_numbers


        profession_numbers = {}
        for profession in OpProfession.objects.db_manager('politici').getBasic().values('id', 'odescription'):
            profession_numbers[profession['id']] = { 'name': profession['odescription'], 'count': 0 }
        if profession_id == 0:
            profession_sql = """select pr.id, pr.oid, count(*) as n
              %s %s
              group by pr.id, pr.oid order by n desc""" % (base_sql, clauses_sql)
            cursor.execute(profession_sql, clauses_params)
            for row in cursor.fetchall():
                if row[1] != None:
                    p_id = row[1]
                else:
                    p_id = row[0]
                p_count = int(row[2])
                if p_id in profession_numbers:
                    profession_numbers[p_id]['count'] += p_count
                else:
                    if settings.DEBUG:
                        print "Impossibile trovare profession_id (oid: %s, id: %s)" % (row[1], row[0])

            results['professions'] = profession_numbers


        education_numbers = {}
        for education in OpEducationLevel.objects.db_manager('politici').getBasic().values('id', 'description'):
            education_numbers[education['id']] = { 'name': education['description'], 'count': 0 }
        if education_id == 0:
            education_sql = """select e.id, e.oid, count(*) as n
              %s %s
              group by e.id, e.oid order by n desc""" % (base_sql, clauses_sql)
            cursor.execute(education_sql, clauses_params)
            for row in cursor.fetchall():
                if row[1] != None:
                    e_id = row[1]
                else:
                    e_id = row[0]
                e_count = int(row[2])

                if e_id in education_numbers:
                    education_numbers[e_id]['count'] += e_count
                else:
                    if settings.DEBUG:
                        print "Impossibile trovare education_id (oid: %s, id: %s)" % (row[0], row[1])

            results['educations'] = education_numbers


        return { 'filters': filters, 'results': results }



class OpInstitutionCharge(models.Model):
    content = models.OneToOneField('OpOpenContent', primary_key=True, db_column='content_id')
    politician = models.ForeignKey('OpPolitician')
    institution = models.ForeignKey('OpInstitution')
    charge_type = models.ForeignKey('OpChargeType')
    location = models.ForeignKey('OpLocation', null=True, blank=True)
    constituency = models.ForeignKey('OpConstituency', null=True, blank=True)
    party = models.ForeignKey('OpParty')
    group = models.ForeignKey('OpGroup')
    date_start = models.DateField(null=True, blank=True)
    date_end = models.DateField(null=True, blank=True)
    description = models.CharField(max_length=255, blank=True)
    minint_verified_at = models.DateTimeField(null=True, blank=True)
    objects = OpInstitutionChargeManager()

    class Meta:
        db_table = u'op_institution_charge'
        managed = False

    def getExtendedTextualRepresentation(self):
        return self.getTextualRepresentation(extended=True)

    def getTextualRepresentation(self, extended=False):
        """build a textual representation for the charge
        extended may take the value true, if extended infos are required"""
        s = ""
        # start and end date
        if self.date_start.month == 1 and self.date_start.day == 1:
            s += "dal %s " % self.date_start.year
        else:
            s += "dal %02d/%02d/%04d " % (self.date_start.day, self.date_start.month, self.date_start.year)

        if self.date_end is not None:
            if self.date_end.month == 1 and self.date_end.day == 1:
                s += "al %s " % self.date_end.year
            else:
                s += "al %02d/%02d/%04d " % (self.date_end.day, self.date_end.month, self.date_end.year)

        # charge type and institution
        institution_name = self.institution.name
        charge_type = self.charge_type.short_name

        if institution_name == 'Governo Nazionale':
            s += "%s %s" % (charge_type, self.description)

        elif (institution_name == 'Commissione Europea' or
              institution_name == 'Parlamento Europeo'):
            s += "%s %s" % (charge_type, institution_name)

        elif (institution_name == 'Senato della Eepubblica' or
              institution_name == 'Camera dei Deputati'):
            if (charge_type != 'Senatore' and
                charge_type != 'Deputato' and
                charge_type != 'Senatore a vita'):
                s += "%s %s %s" % (charge_type, institution_name, self.description)
            else:
                s += "%s" % (charge_type,)

        elif (institution_name == 'Giunta Regionale' or
              institution_name == 'Giunta Provinciale' or
              institution_name == 'Giunta Comunale'):
            s += "%s" % (charge_type,)
            if charge_type == 'Presidente':
                s += " Giunta"
            if extended and\
               (charge_type == 'Assessore' or charge_type == 'Sottosegretario'):
                s += " %s" % (self.description,)
            s += " %s %s " % (institution_name, self.location.name)

        elif (institution_name == 'Consiglio Regionale' or
              institution_name == 'Consiglio Provinciale' or
              institution_name == 'Consiglio Comunale'):
            s += "%s" % (charge_type,)
            if charge_type == 'Presidente' or charge_type == 'Vicepresidente':
                s += " Consiglio"
            if extended and charge_type == 'Assessore':
                s += " %s" % (self.description,)
            s += " %s %s " % (institution_name, self.location.name)

        else:
            s += "%s" % charge_type


        # party, for executive charges
        executive_institutions = ('Commissione Europea', 'Governo Nazionale',
                                  'Giunta Regionale', 'Giunta Provinciale', 'Giunta Comunale')
        if institution_name in executive_institutions:
            if self.party.name.lower() != 'non specificato':
                s += "(Partito: %s)" % (self.party.getNormalizedAcronymOrName())

        # group or election party, for elective charges
        elective_institutions = ('Parlamento Europea', 'Camera dei Deputati', 'Senato della Repubblica',
                                 'Consiglio Regionale', 'Consiglio Provinciale', 'Consiglio Comunale')
        if (institution_name in elective_institutions and
            self.charge_type.name.lower() != 'senatore a vita'):
            if self.group.name.lower() != 'non specificato':
                s += "(Gruppo: %s) " % (self.group.getNormalizedAcronymOrName())
            elif self.party.name.lower() != 'non specificato':
                s += "(Lista elettorale: %s) " % (self.party.getNormalizedAcronymOrName())


        if extended:
            if (self.constituency is not None and
                self.charge_type.name.lower() != 'senatore a vita' and
                self.institution.name.lower() != 'governo nazionale'):
                s += " Eletto nella circoscrizione %s" % (self.constituency.name,)

        return s



class OpPoliticalCharge(models.Model):
    content = models.OneToOneField('OpOpenContent', primary_key=True, db_column='content_id')
    charge_type = models.ForeignKey('OpChargeType')
    politician = models.ForeignKey('OpPolitician')
    location = models.ForeignKey('OpLocation')
    party = models.ForeignKey('OpParty')
    date_start = models.DateField(null=True, blank=True)
    date_end = models.DateField(null=True, blank=True)
    description = models.CharField(max_length=255, blank=True)
    current = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = u'op_political_charge'
        managed = False

    def getTextualRepresentation(self, extended=False):
        """build a textual representation for the charge
        extended may take the value true, if extended infos are required"""
        s = u""
        # start and end date
        if self.date_start is not None:
            if self.date_start.month == 1 and self.date_start.day == 1:
                s += u"dal %s " % self.date_start.year
            else:
                s += u"dal %02d/%02d/%04d " % (self.date_start.day, self.date_start.month, self.date_start.year)

        if self.date_end is not None:
            if self.date_end.month == 1 and self.date_end.day == 1:
                s += u"al %s " % self.date_end.year
            else:
                s += u"al %02d/%02d/%04d " % (self.date_end.day, self.date_end.month, self.date_end.year)
            s += u"è stato "
        else:
            s += u"è "

        # charge type and party
        charge_type = self.charge_type.name
        if charge_type == 'iscritto':
            s += u"%s" % (smart_unicode(charge_type),)
        else:
            s += u"%s" % (self.description and smart_unicode(self.description),)

        s += u" - %s" % (self.party and smart_unicode(self.party.getNormalized().getName()))

        if self.location.location_type.name == 'Regione':
            s += u" (regione %s) " % (smart_unicode(self.location.name),)
        elif self.location.location_type.name == 'Provincia':
            s += u" (provincia di %s) " % (smart_unicode(self.location.name),)
        elif self.location.location_type.name == 'Comune':
            s += u" (comune di %s [%s]) " % (smart_unicode(self.location.name), self.location.prov)

        return s



class OpOrganization(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=255, blank=True)
    url = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = u'op_organization'
        managed = False



class OpOrganizationCharge(models.Model):
    content = models.OneToOneField('OpOpenContent', primary_key=True, db_column='content_id')
    politician = models.ForeignKey('OpPolitician')
    date_start = models.DateField(null=True, blank=True)
    date_end = models.DateField(null=True, blank=True)
    charge_name = models.CharField(max_length=255, blank=True)
    organization = models.ForeignKey('OpOrganization', null=True, blank=True)
    current = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = u'op_organization_charge'
        managed = False


    def getTextualRepresentation(self, extended=False):
        """build a textual representation for the charge
        extended may take the value true, if extended infos are required"""
        s = u""
        # start and end date
        if self.date_start.month == 1 and self.date_start.day == 1:
            s += u"dal %s " % self.date_start.year
        else:
            s += u"dal %02d/%02d/%04d " % (self.date_start.day, self.date_start.month, self.date_start.year)

        if self.date_end is not None:
            if self.date_end.month == 1 and self.date_end.day == 1:
                s += u"al %s " % self.date_end.year
            else:
                s += u"al %02d/%02d/%04d " % (self.date_end.day, self.date_end.month, self.date_end.year)
            s += u"è stato "
        else:
            s += u"è "

        # charge type and party
        if self.charge_name is not None:
            s += u"%s" % (smart_unicode(self.charge_name),)
        else:
            s += u"appartenente"

        s += u" %s (%s)" %\
             (smart_unicode(self.organization.name), self.organization.url and smart_unicode(self.organization.url))

        return s



class OpOrganizationTag(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=32)

    class Meta:
        db_table = u'op_organization_tag'
        managed = False



class OpOrganizationHasOpOrganizationTag(models.Model):
    organization_tag = models.ForeignKey('OpOrganizationTag')
    organization = models.ForeignKey('OpOrganization')

    class Meta:
        db_table = u'op_organization_has_op_organization_tag'
        managed = False



class OpResourcesType(models.Model):
    id = models.IntegerField(primary_key=True)
    denominazione = models.CharField(max_length=80, blank=True, db_column='resource_type')

    class Meta:
        db_table = u'op_resources_type'
        managed = False



class OpResources(models.Model):
    content = models.OneToOneField('OpOpenContent', primary_key=True, db_column='content_id')
    politician = models.ForeignKey('OpPolitician')
    resources_type = models.ForeignKey('OpResourcesType')
    valore = models.CharField(max_length=255, blank=True)
    descrizione = models.TextField(blank=True)

    @property
    def resources_type_denominazione(self):
        return self.resources_type.denominazione

    class Meta:
        db_table = u'op_resources'
        managed = False
    


class OpLocationType(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=96)
    class Meta:
        db_table = u'op_location_type'
        managed = False
    def __unicode__(self):
        return self.name


class OpLocationQuerySet(QuerySet):

    _cache = {}
    def _location_query(self, method, key, key_field='pk'):
        """ returns a get cached query"""
        cache_key = "%s_by_%s_%s" % (method, key_field, key)
        if cache_key not in OpLocationQuerySet._cache:
            OpLocationQuerySet._cache[cache_key] = getattr(self, method)().get(**{key_field:key})
        return OpLocationQuerySet._cache[cache_key]


    def regioni(self):
        return self.filter(location_type_id=OpLocation.REGION_TYPE_ID)

    def regione(self, id, codename='op'):
        try:
            return getattr(self, {
                                     'op': 'regione_from_id',
                                     'istat': 'regione_from_istat_id',
                                     }[codename])( id )
        except KeyError:
            raise Exception("'%s' is invalid codename for location" % codename)


    def regione_from_location(self, comune_or_provincia):
        """return an Location object that contains provided location"""
        return self._location_query('regioni', comune_or_provincia.regional_id, 'regional_id')

    def regione_from_id(self, id):
        """return an Location region object from primary key"""
        return self._location_query('regioni', id)

    def regione_from_istat_id(self, id):
        """return an Location region object, from the istat regional_id"""
        return self.regioni().get(regional_id = id )

    def province(self):
        return self.filter(location_type_id=OpLocation.PROVINCE_TYPE_ID)

    def provincia(self, id, codename='op'):
        try:
            return getattr(self, {
                                     'op': 'provincia_from_id',
                                     'istat': 'provincia_from_istat_id',
                                     }[codename])( id )
        except KeyError:
            raise Exception("'%s' is invalid codename for location" % codename)

    def provincia_from_location(self, comune):
        """return an Location object that contains provided location"""
        return self._location_query('province', comune.provincial_id, 'provincial_id')

    def provincia_from_id(self, id):
        """return an Location province object from primary key"""
        return self._location_query('province', id)

    def provincia_from_istat_id(self, id):
        """return an Location object, from the istat provincial_id"""
        return self._location_query('province', id, 'provincial_id')

    def comuni(self):
        return self.filter(location_type_id=OpLocation.CITY_TYPE_ID)

    def comune_from_id(self, id):
        """return an Location city object from primary key"""
        return self._location_query('comuni', id)

    def comune_from_istat_id(self, id):
        """return an Location object, from the istat city_id"""
        return self._location_query('comuni', id, 'city_id')

    def comune_from_minint_id(self, minint_id):
        """
        return an Location object, from the minint codes
        minint codes is packed: 2A3A4A
        the argument length is validated
        codes are unpacked from the argument
        """
        if len(minint_id) != 9:
            raise Exception('minint_id code must be exactly 9 characters long: %s is %s char-long' % (id, len(minint_id),))
        regional_code = int(id[:2])
        provincial_code = int(id[2:5])
        city_code = int(id[5:])

        return self.comuni().get(minint_regional_code=regional_code,
                                 minint_provincial_code=provincial_code,
                                 minint_city_code=city_code)

    def comune(self, id, codename='op'):
        try:
            return getattr(self, {
                                     'op': 'comune_from_id',
                                     'istat': 'comune_from_istat_id',
                                     'minint': 'comune_from_minint_id'
                                 }[codename])( id )
        except KeyError:
            raise Exception("'%s' is invalid codename for location" % codename)



class OpLocationManager(models.Manager):

    def get_query_set(self):
        return OpLocationQuerySet(self.model, using=self._db)

    def regioni(self): return self.get_query_set().regioni()
    def regione(self, territorio, codename='op'): return self.get_query_set().regione(territorio, codename)
    def regione_from_id(self, id): return self.regione(id, codename='op')
    def regione_from_istat_id(self, id): return self.regione(id, codename='istat')
    def province(self): return self.get_query_set().province()
    def provincia(self, territorio, codename='op'): return self.get_query_set().provincia(territorio, codename)
    def provincia_from_id(self, id): return self.provincia(id, codename='op')
    def provincia_from_istat_id(self, id): return self.provincia(id, codename='istat')
    def comuni(self): return self.get_query_set().comuni()
    def comune(self, territorio_id, codename='op'): return self.get_query_set().comune(territorio_id, codename=codename)
    def comune_from_id(self, id): return self.comune(id, codename='op')
    def comune_from_istat_id(self, id): return self.comune(id, codename='istat')
    def comune_from_minint_id(self, id): return self.comune(id, codename='minint')

    def retrieve_by_type(self, location_type, location_id, codename='op'):
        if isinstance(location_type, (int,long)):
            if location_type == OpLocation.CITY_TYPE_ID:
                return self.comune(location_id, codename=codename)
            if location_type == OpLocation.PROVINCE_TYPE_ID:
                return self.comune(location_id, codename=codename)
            if location_type == OpLocation.REGION_TYPE_ID:
                return self.regione(location_id, codename=codename)
        else:
            if location_type == 'regional':
                return self.regione(location_id, codename=codename)
            if location_type == 'provincial':
                return self.provincia(location_id, codename=codename)
            elif location_type == 'city':
                return self.comune(location_id, codename=codename)

        raise Exception('wrong location_type parameters %s not in (regional, provincial, city)' % location_type)



class OpLocation(models.Model):

    CITY_TYPE_ID = 6
    PROVINCE_TYPE_ID = 5
    REGION_TYPE_ID = 4

    id = models.IntegerField(primary_key=True)
    location_type = models.ForeignKey('OpLocationType')
    name = models.CharField(max_length=255, blank=True)
    macroregional_id = models.IntegerField(null=True, blank=True)
    regional_id = models.IntegerField(null=True, blank=True)
    provincial_id = models.IntegerField(null=True, blank=True)
    city_id = models.IntegerField(null=True, blank=True)
    prov = models.CharField(max_length=2, blank=True, null=True)
    inhabitants = models.IntegerField(null=True, blank=True)
    last_charge_update = models.DateTimeField(null=True, blank=True)
    alternative_name = models.CharField(max_length=255, blank=True, null=True)
    minint_regional_code = models.IntegerField(null=True, blank=True)
    minint_provincial_code = models.IntegerField(null=True, blank=True)
    minint_city_code = models.IntegerField(null=True, blank=True)
    date_start = models.DateField(null=True, blank=True)
    date_end = models.DateField(null=True, blank=True)
    new_location_id = models.IntegerField(null=True, blank=True)
    gps_lat = models.FloatField(null=True, blank=True)
    gps_lon = models.FloatField(null=True, blank=True)

    objects = OpLocationManager()

    class Meta:
        db_table = u'op_location'
        managed = False

    def __unicode__(self):
        bits = [self.name]
        if self.location_type_id == OpLocation.CITY_TYPE_ID:
            bits.insert(0,u'Comune di')
            bits.append(u'(%s)' % self.prov)
        elif self.location_type_id == OpLocation.PROVINCE_TYPE_ID:
            bits.insert(0,u'Provincia di')
        elif self.location_type_id == OpLocation.REGION_TYPE_ID:
            bits.insert(0,u'Regione')

        return u" ".join(bits)

    @property
    def minint_id(self):
        """
        regional_code = int(minint_id[:2])
        provincial_code = int(minint_id[2:5])
        city_code = int(minint_id[5:])
        """
        return "{0}{1}{2}".format(
            str(self.minint_regional_code).zfill(2),
            str(self.minint_provincial_code).zfill(3),
            str(self.minint_city_code).zfill(4)
        )

    def getConstituencies(self, election_type=None, prov_id=None):
        """docstring for getConstituency"""

        if prov_id is None:
            prov_id = self.getProvince().id

        kwargs = {
            'opconstituencylocation__location_id': prov_id
        }
        if election_type:
            if isinstance(election_type, (int,long)):
                kwargs['election_type__id']= election_type
            else:
                kwargs['election_type__name']= election_type
        return OpConstituency.objects.db_manager(DBNAME).filter(**kwargs)

    def getConstituency(self, election_type, prov_id=None):

        try:
            return self.getConstituencies(election_type, prov_id)[0]
        except IndexError:
            raise OpConstituency.DoesNotExist

    def getNationalReps(self, election_type, prov_id=None):
        """docstring for getNationalReps"""

        constituency = self.getConstituency(election_type, prov_id)
        charges = OpInstitutionCharge.objects.db_manager(DBNAME).filter(
            date_end=None,
            constituency__id=constituency.id,
            content__deleted_at=None
        ).order_by('politician__last_name')
        reps = []
        for charge in charges:
            reps.append({
                'first_name': charge.politician.first_name,
                'last_name': charge.politician.last_name,
                'charge': charge.charge_type.name,
                'charge_id': charge.content_id,
                'politician_id': charge.politician.content_id,
                })
        return {
            'constituency': constituency.name,
            'representatives': reps
        }

    def getLocalReps(self, institution_name):
        """docstring for getLocalReps"""

        charges = OpInstitutionCharge.objects.db_manager(DBNAME).filter(
            institution__name=institution_name,
            location__id=self.id,
            date_end=None,
            content__deleted_at=None,
            ).order_by('charge_type__priority', 'politician__last_name')
        reps  = []

        for charge in charges:
            reps.append({
                'first_name': charge.politician.first_name,
                'last_name': charge.politician.last_name,
                'charge': charge.charge_type.name,
                'charge_id': charge.content_id,
                'politician_id': charge.politician.content_id,
                })
        return reps

